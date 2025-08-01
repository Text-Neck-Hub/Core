

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket Image Stream</title>
    </head>
    <body>
        <h1>WebSocket Image Stream with MediaPipe</h1>
        <video id="video" width="320" height="240" autoplay></video>
        <canvas id="canvas" width="320" height="240"></canvas>
        <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            let ws;
            let lastImg = null;

            // Get webcam
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(stream => {
                    video.srcObject = stream;
                    ws = new WebSocket("ws://localhost:8000/ws");
                    ws.onmessage = (event) => {
                        let data = JSON.parse(event.data);
                        if (data.has_angle) {
                            lastImg = new Image();
                            lastImg.onload = function() {
                                ctx.clearRect(0, 0, 320, 240); // 캔버스 초기화
                                ctx.drawImage(lastImg, 0, 0, 320, 240);
                            };
                            lastImg.src = 'data:image/jpeg;base64,' + data.img;
                        }
                    };
                    setInterval(() => {
                        ctx.drawImage(video, 0, 0, 320, 240); // 웹캠 프레임만 그림
                        let dataURL = canvas.toDataURL('image/jpeg');
                        let base64 = dataURL.split(',')[1];
                        ws.send(base64);
                    }, 100); // 10fps
                });
        </script>
    </body>
</html>
"""
