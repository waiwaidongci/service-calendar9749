import {request} from './client.js';
export const loadAll=async()=>Object.fromEntries(await Promise.all([['sources','/sources'],['periods','/periods'],['policies','/policies'],['runs','/runs'],['schedules','/schedules'],['deliveries','/deliveries'],['audits','/audits'],['publications','/publications'],['accounts','/privacy/accounts']].map(async([k,p])=>[k,await request(p)])));
export const saveSource=(data,id)=>request('/sources'+(id?'/'+id:''),id?'PUT':'POST',{data});
export const savePolicy=data=>request('/policies','POST',{data});
export const submitRun=data=>request('/runs','POST',data);
export const approveRun=(id,note)=>request('/runs/'+id+'/approve','POST',{note});
export const publishRun=(id,key)=>request('/runs/'+id+'/publish','POST',{idempotency_key:key});
