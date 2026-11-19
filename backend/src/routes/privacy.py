from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import Response
from src.config.database import database
from src.controllers.auth import current,admin
from src.models.privacy import Publication
from src.schemas.requests import BudgetInput
from src.services.privacy import accounts,set_budget
from src.services.export import csv_text
from src.utils.serialize import row
router=APIRouter()
@router.get('/publications')
def publications(db=Depends(database),u=Depends(current)): return [row(x) for x in db.query(Publication).order_by(Publication.id.desc()).limit(100).all()]
@router.get('/publications/{id}/csv')
def download(id:int,db=Depends(database),u=Depends(current)):
 obj=db.get(Publication,id)
 if not obj: raise HTTPException(404,'发布不存在')
 return Response(csv_text(obj.result),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="publication-{id}.csv"'})
@router.get('/privacy/accounts')
def privacy_accounts(db=Depends(database),u=Depends(current)): return [row(x) for x in accounts(db)]
@router.post('/privacy/accounts')
def privacy_budget(b:BudgetInput,db=Depends(database),u=Depends(admin)): return row(set_budget(db,u,b.draft_key,b.budget))
