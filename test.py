from src.scraper import start_extraction

print("A iniciar o teste do motor...")
link = "https://www.diy.ie/departments/fortia-vertical-2-panel-unglazed-contemporary-pine-veneer-internal-clear-pine-door-h-1981mm-w-838mm-t-35mm/42641_BQ.prd"

start_extraction(link)
print("Teste concluído!")
