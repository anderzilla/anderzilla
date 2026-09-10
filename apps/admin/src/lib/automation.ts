import {request} from './cms';
export type AutomationProcess={id:string;version:number;title:string;description:string;available:boolean;executorConnected:boolean;executionMode:string;status:string;role?:string};
export type AutomationInput={market:'br'|'intl'|'global';language:'pt-BR'|'en';notes?:string;periodStart?:string;periodEnd?:string;targetUrl?:string};
export type AutomationRun={id:string;processId:string;status:string;version:number;attempt:number;parentRunId?:string|null;retryRunId?:string|null;createdAt:string;updatedAt?:string;startedAt?:string|null;finishedAt?:string|null;input:AutomationInput;executionMode:string;externalDispatched:boolean;requestedBy?:string;history?:Array<Record<string,unknown>>;error?:string|null|{code:string;message:string};deliveryCount?:number;fencingToken?:number;leaseId?:string;leasedAt?:string|null;leaseExpiresAt?:string|null;result?:unknown;resultHash?:string};
export type AutomationPreview={process:AutomationProcess;input:AutomationInput;executionMode:string;externalDispatchEnabled:boolean;costEstimate:null|Record<string,unknown>;warnings:string[]};
export type AutomationSummary={counts:Record<string,number>;executorConnected:boolean;costs:null|Record<string,unknown>};
export const automationAPI={
 processes:(token:string)=>request<{items:AutomationProcess[];externalDispatchEnabled:boolean}>('/admin/automation/processes',token),
 runs:(token:string,cursor?:string)=>request<{items:AutomationRun[];nextCursor?:string|null}>('/admin/automation/runs'+(cursor?'?cursor='+encodeURIComponent(cursor):''),token),
 run:(token:string,id:string)=>request<AutomationRun>('/admin/automation/runs/'+encodeURIComponent(id),token),
 summary:(token:string)=>request<AutomationSummary>('/admin/automation/summary',token),
 preview:(token:string,body:{processId:string;processVersion:number;input:AutomationInput})=>request<AutomationPreview>('/admin/automation/runs/preview',token,{method:'POST',body:JSON.stringify(body)}),
 create:(token:string,body:{processId:string;processVersion:number;input:AutomationInput;idempotencyKey:string})=>request<AutomationRun>('/admin/automation/runs',token,{method:'POST',body:JSON.stringify(body)}),
 command:(token:string,id:string,command:'cancel'|'retry'|'transition',body:{version:number;reason:string;idempotencyKey:string;action?:string;evidence?:string})=>request<AutomationRun>('/admin/automation/runs/'+encodeURIComponent(id)+'/'+command,token,{method:'POST',body:JSON.stringify(body)})
};
export const runLabels:Record<string,string>={queued:'Na fila',running:'Em andamento manual',dispatching:'Em despacho',awaiting_review:'Aguardando revisão',succeeded:'Concluída',failed:'Falhou',cancel_requested:'Cancelamento solicitado',cancelled:'Cancelada',blocked:'Bloqueada'};
