import re,sys,json
txt=open(sys.argv[1],encoding='utf-8').read().split('\n')
want={'01A':'agua','02A':'saneamiento','04A':'dci','05A':'lactancia','06.1A':'anemia','12A':'vacunas12m','17A':'cred','19A':'hierro','22A':'tgf','36A':'violencia'}
deps=['Amazonas','Áncash','Apurímac','Arequipa','Ayacucho','Cajamarca','Prov. Const. del Callao','Cusco','Huancavelica','Huánuco','Ica','Junín','La Libertad','Lambayeque','Lima Metropolitana','Departamento de Lima','Loreto','Madre de Dios','Moquegua','Pasco','Piura','Puno','San Martín','Tacna','Tumbes','Ucayali','Total']
out={}
starts=[(i,re.search(r'CUADRO N[º°] ?([\d.]+A?)\s*:',l)) for i,l in enumerate(txt)]
starts=[(i,m.group(1)) for i,m in starts if m]
for k,(i,code) in enumerate(starts):
  if code not in want: continue
  end=starts[k+1][0] if k+1<len(starts) else i+80
  key=want[code]; out[key]={'cuadro':code,'title':' '.join(txt[i].split()), 'v':{}}
  for l in txt[i:end]:
    s=l.strip()
    for d in deps:
      if s.startswith(d):
        nums=re.findall(r'\(?-?\d+,\d+\)?',s[len(d):])
        if len(nums)>=5:
          f=lambda x: float(x.strip('()').replace(',','.'))
          out[key]['v'][d]={'y2021':f(nums[0]),'y2022':f(nums[1]),'y2023':f(nums[2]),'y2024':f(nums[3]),'y2025':f(nums[4]),'ref':nums[4].startswith('(')}
        break
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
for k,v in out.items(): print(k,v['cuadro'],len(v['v']),v['v'].get('Cusco'),v['v'].get('Total'))
