@echo off
echo Atualizando dados do projeto São Paulo...

cd C:\Users\fernando.oliveira\Downloads\projetos\agente_projetos
py -m agente_json

echo Enviando para o GitHub...
cd C:\Users\fernando.oliveira\Downloads\projetos
git add saopaulo.json historico.json agente_projetos\saopaulo.json
git commit -m "Atualiza dados São Paulo - %date% %time%"
git push

echo.
echo Pronto! Dashboard atualizado em https://nandomanfredo.github.io/projectview/saopaulo.html
pause
