var setUpCanvasDrawing = function () {
    var drawingCanvas = document.getElementById('drawing-canvas');
    var drawingContext = drawingCanvas.getContext('2d');

    drawingContext.fillStyle = '#FFFFFF';
    drawingContext.fillRect(0, 0, 224, 224);

    drawingCanvas.addEventListener('mousedown', function (e) {
        paint = true;
        drawStartPos.set(e.offsetX, e.offsetY)
    });
    drawingCanvas.addEventListener('mouseup', function (e) {
        paint = false
    });
    drawingCanvas.addEventListener('mouseleave', function (e) {
        paint = false
    });
    drawingCanvas.addEventListener('mousemove', function (e) {
        if (paint) {
            draw(drawingContext, e.offsetX, e.offsetY);
        }
    });
}

var clearCanvas = function () {
    var drawingCanvas = document.getElementById('drawing-canvas');
    var drawingContext = drawingCanvas.getContext('2d');
    drawingContext.clearRect(0, 0, 224, 224);
    drawingContext.beginPath();
    drawingContext.fillStyle = '#FFFFFF';
    drawingContext.fillRect(0, 0, 224, 224);
};

var draw = function (drawContext, x, y) {
    drawContext.moveTo(drawStartPos.x, drawStartPos.y);
    drawContext.strokeStyle = '#000000';
    drawContext.lineTo(x, y);
    drawContext.stroke();
    drawStartPos.set(x, y);
}
