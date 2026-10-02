go into proxy folder
cd "C:\Users\moir0921\Documents\irfan\Local LLM\llm-proxy"

activate the proxy environment
.\.venv\Scripts\Activate.ps1

start proxy server
python -m uvicorn main:app --host 0.0.0.0 --port 9000

verify proxy from powershell
curl.exe http://localhost:9000/health

restart podman
podman rm -f local-llm

create image
podman build -t localhost/local-llm:latest . 

run image
podman run -d `
  --name local-llm `
  --env-file .env `
  -p 8000:8000 `
  localhost/local-llm:latest

check podman
podman ps
podman ps -

check log
podman logs local-llm

run local llm locally
uvicorn app.main:app --reload                              
python -m uvicorn app.main:app --host 0.0.0.0 --port 7000 --reload

build frontend repo
npm run build