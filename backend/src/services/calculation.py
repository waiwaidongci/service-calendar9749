from datetime import datetime,timedelta,time
from zoneinfo import ZoneInfo
from collections import defaultdict
from src.services.validation import validate_source,validate_policy
def business_minutes(opened,closed,policy):
 zone=ZoneInfo(policy['timezone']);a=datetime.fromisoformat(opened).astimezone(zone);b=datetime.fromisoformat(closed).astimezone(zone)
 if b<a:raise ValueError('结束时间早于开始时间')
 day=a.date();total=0
 while day<=b.date():
  if day.weekday() in policy['weekdays'] and day.isoformat() not in policy.get('holidays',[]):
   midnight=datetime.combine(day,time(),zone)
   for start,end in policy['windows']:
    lo=max(a,midnight+timedelta(minutes=start));hi=min(b,midnight+timedelta(minutes=end));total+=max(0,(hi-lo).total_seconds()/60)
  day+=timedelta(days=1)
 return total
def calculate(sources,policy):
 validate_policy(policy);pivot=defaultdict(lambda:{'count':0,'minutes':0,'overdue':0});rows=[]
 for s in sources:
  validate_source(s)
  if s['priority'] not in policy['sla_minutes']:raise ValueError('优先级无SLA口径：'+s['priority'])
  mins=business_minutes(s['opened'],s['closed'],policy);limit=policy['sla_minutes'][s['priority']];k=(s['period'],s['department'],s['priority']);p=pivot[k];p['count']+=1;p['minutes']+=mins;p['overdue']+=int(mins>limit)
 for (period,dept,priority),p in sorted(pivot.items()):rows.append({'月份':period,'小组':dept,'优先级':priority,'样本数':p['count'],'业务分钟合计':p['minutes'],'平均业务分钟':p['minutes']/p['count'],'超时数':p['overdue'],'超时率':p['overdue']/p['count']})
 return {'summary':{'样本数':len(sources),'业务分钟合计':sum(p['minutes'] for p in pivot.values()),'超时数':sum(p['overdue'] for p in pivot.values()),'时区':policy['timezone']},'rows':rows,'method':'ISO时区转换至业务日历时区后，逐日求开始/结束区间与不重叠工作时窗交集；排除非工作日、显式假日与午休。恰等于SLA阈值不算超时。','warnings':['统计合成已结束样本；不包含未关闭请求，也不承诺实时事件提醒。']}
