import openpyxl,json,sys,unicodedata
def norm(x): return ''.join(c for c in unicodedata.normalize('NFD',x) if unicodedata.category(c)!='Mn').strip()
base=sys.argv[1]
DEPS=['Amazonas','Áncash','Apurímac','Arequipa','Ayacucho','Cajamarca','Cusco','Huancavelica','Huánuco','Ica','Junín','La Libertad','Lambayeque','Lima Metropolitana 1/','Prov. Const. del Callao','Lima 2/','Loreto','Madre de Dios','Moquegua','Pasco','Piura','Puno','San Martín','Tacna','Tumbes','Ucayali','Nacional']
def grab(path,sheet_idx,start_after='Departamentos',ncols=10):
  ws=openpyxl.load_workbook(path,data_only=True).worksheets[sheet_idx]
  out={}
  for r in ws.iter_rows(values_only=True):
    r=[c for c in r if c is not None]
    name=next((d for d in DEPS if isinstance(r[0],str) and norm(r[0])==norm(d)),None) if r else None
    if name and len(r)>ncols and name.replace(' 1/','').replace(' 2/','') not in out:
      nums=[x for x in r[1:] if isinstance(x,(int,float))]
      out[name.replace(' 1/','').replace(' 2/','')]=[round(x,1) for x in nums[:ncols]]
  return out
pob=grab(base+'/03_FGT de Pobreza 2016-2025_informe.xlsx',0)
gas=grab(base+'/01_Gastos reales_nominales_2016_2025_informe.xlsx',0)
import glob
ing=grab(glob.glob(base+'/01_Ingresos*')[0],0)
json.dump({'pobreza':pob,'gasto_real':gas,'ingreso_real':ing,'years':list(range(2016,2026))},open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
for k,v in [('pob',pob),('gas',gas),('ing',ing)]: print(k,len(v),v.get('Cusco'),v.get('Nacional'))
