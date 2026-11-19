import math,time
from random import SystemRandom
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from src.models.run import Run
from src.models.privacy import PrivacyAccount,Publication
from src.services.audit import log
from src.config.settings import DP_EPSILON,DP_BUDGET
_rng=SystemRandom()
def _laplace(scale):
 u=_rng.random()-0.5
 return 0.0 if u==0 else -scale*math.copysign(math.log1p(-2*abs(u)),u)
def _noisy_rows(rows,epsilon):
 scale=1.0/epsilon;out=[]
 for r in rows:
  overdue=int(r['超时数']);on_time=int(r['样本数'])-overdue
  k=max(0,round(overdue+_laplace(scale)));o=max(0,round(on_time+_laplace(scale)));n=k+o
  out.append({'月份':r['月份'],'小组':r['小组'],'优先级':r['优先级'],'样本数':n,'超时数':k,'超时率':k/n if n else 0})
 return out
def _replay(db,key,run_id):
 hit=db.query(Publication).filter_by(idempotency_key=key).first()
 if hit:
  if hit.run_id!=run_id: raise HTTPException(409,'幂等键已被其他报告使用')
  return hit
 return None
def _ensure_accounts(db,keys):
 have={a.draft_key for a in db.query(PrivacyAccount).filter(PrivacyAccount.draft_key.in_(keys)).all()}
 for k in keys:
  if k not in have:
   try:
    with db.begin_nested(): db.add(PrivacyAccount(draft_key=k,budget=DP_BUDGET,spent=0.0))
   except IntegrityError: pass
def publish(db,user,run_id,key):
 obj=db.get(Run,run_id)
 if not obj: raise HTTPException(404,'报告不存在')
 hit=_replay(db,key,run_id)
 if hit: return hit
 if obj.status!='completed' or not obj.approved: raise HTTPException(409,'仅可发布已复核的完成报告')
 if not obj.draft_keys: raise HTTPException(409,'该报告缺少底稿编号字段，仅可内部使用，不可外发')
 rows=(obj.result or {}).get('rows') or []
 if not rows: raise HTTPException(409,'报告无透视结果，不可发布')
 keys=sorted(set(obj.draft_keys))
 _ensure_accounts(db,keys)
 accounts={a.draft_key:a for a in db.query(PrivacyAccount).filter(PrivacyAccount.draft_key.in_(keys)).with_for_update().all()}
 hit=_replay(db,key,run_id)
 if hit: return hit
 lacking=[k for k in keys if accounts[k].spent+DP_EPSILON>accounts[k].budget+1e-9]
 if lacking: raise HTTPException(409,f'底稿隐私额度不足，整份拒发：{lacking[0]} 等 {len(lacking)} 份底稿剩余额度不足 {DP_EPSILON}')
 result={'name':obj.name,'checksum':obj.checksum,'policy_version':obj.snapshot['policy'].get('version'),'epsilon':DP_EPSILON,'rows':_noisy_rows(rows,DP_EPSILON),'method':'差分隐私发布：按预先约定的小组（月份×小组×优先级）对超时数与未超时数分别施加拉普拉斯噪声（尺度1/ε），样本数与超时数由加噪计数推出；非负与取整为后处理，不额外消耗额度。','warnings':['发布值为加噪统计结果，不可用于推断单笔底稿是否超时。']}
 pub=Publication(run_id=obj.id,idempotency_key=key,epsilon=DP_EPSILON,result=result,created=time.time(),actor=user.email)
 db.add(pub)
 for k in keys: accounts[k].spent=round(accounts[k].spent+DP_EPSILON,9)
 log(db,user.email,'run.publish',f'报告{obj.id} 幂等键{key}')
 try: db.commit()
 except IntegrityError:
  db.rollback();hit=_replay(db,key,run_id)
  if hit: return hit
  raise HTTPException(409,'发布冲突，请使用同一幂等键重试')
 return pub
def accounts(db): return db.query(PrivacyAccount).order_by(PrivacyAccount.draft_key).all()
def set_budget(db,user,draft_key,budget):
 obj=db.query(PrivacyAccount).filter_by(draft_key=draft_key).with_for_update().first()
 if not obj: obj=PrivacyAccount(draft_key=draft_key,budget=budget,spent=0.0);db.add(obj)
 elif budget<obj.spent: raise HTTPException(409,'约定额度不可低于已消耗额度')
 else: obj.budget=budget
 log(db,user.email,'privacy.budget',f'{draft_key}={budget}');db.commit();return obj
