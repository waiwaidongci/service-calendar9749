import math
from src.config.settings import CONFIG
def number(value,name,minimum=0,integer=False):
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<minimum or (integer and int(value)!=value): raise ValueError(name+'数值不合法')
 return value
def validate_source(d):
 if not isinstance(d,dict) or set(d)!=set(CONFIG['fields']): raise ValueError('底稿字段必须与业务字段一致')
 for key in ('period','department'):
  if not isinstance(d[key],str) or not 1<=len(d[key])<=100: raise ValueError(key+'不能为空或过长')
 from datetime import datetime
 from zoneinfo import ZoneInfo
 try:
  a=datetime.fromisoformat(d['opened']);b=datetime.fromisoformat(d['closed'])
 except Exception: raise ValueError('时间须为ISO格式')
 if not a.tzinfo or not b.tzinfo or b<a or (b-a).total_seconds()>366*86400: raise ValueError('时间须带时区、结束不早于开始且范围不超过366天')
 if not isinstance(d['priority'],str) or not d['priority']:raise ValueError('优先级不能为空')
def validate_policy(d):
 if not isinstance(d,dict) or not isinstance(d.get('version'),str) or not 2<=len(d['version'])<=120: raise ValueError('口径版本名不合法')
 from zoneinfo import ZoneInfo
 from datetime import date
 try:ZoneInfo(d['timezone'])
 except Exception:raise ValueError('时区无效')
 if not isinstance(d.get('weekdays'),list) or not d['weekdays'] or any(type(x)!=int or not 0<=x<=6 for x in d['weekdays']):raise ValueError('工作日需为0到6的数组')
 windows=d.get('windows')
 if not isinstance(windows,list) or not windows or len(windows)>12 or any(not isinstance(x,list) or len(x)!=2 or any(type(t)!=int for t in x) for x in windows):raise ValueError('工作时窗需为最多12个二元素整数数组')
 prev=-1
 for a,b in sorted(windows):
  if type(a)!=int or type(b)!=int or not 0<=a<b<=1440 or a<prev:raise ValueError('工作时窗必须不重叠且分钟范围0到1440')
  prev=b
 if not isinstance(d.get('holidays',[]),list) or len(d.get('holidays',[]))>366:raise ValueError('假日需为不超过366项的数组')
 for x in d.get('holidays',[]):
  try:date.fromisoformat(x)
  except Exception:raise ValueError('假日需为ISO日期')
 if not isinstance(d.get('sla_minutes'),dict) or not d['sla_minutes']:raise ValueError('SLA优先级阈值不能为空')
 for v in d['sla_minutes'].values():number(v,'SLA分钟',minimum=1)
