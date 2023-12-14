cd visualizer/server
source setup.sh
flask run --host 0.0.0.0 --port 52000 &

cd ../client
npm install --save-dev webpack --ignore-scripts
npm run build
cd dist
python -m http.server 8001