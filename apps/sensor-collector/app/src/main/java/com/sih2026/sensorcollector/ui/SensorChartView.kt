package com.sih2026.sensorcollector.ui

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.DashPathEffect
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Path
import android.graphics.Shader
import android.util.AttributeSet
import android.view.View
import java.util.Locale

class SensorChartView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private var chartTitle: String = "Sensor Telemetry"
    private var unitLabel: String = "m/s²"
    private var dataPoints: List<Pair<Float, Float>> = emptyList() // (timeSec, value)

    private val linePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#00E5FF")
        strokeWidth = 4f
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.ROUND
        strokeJoin = Paint.Join.ROUND
    }

    private val gridPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#24344D")
        strokeWidth = 1.5f
        style = Paint.Style.STROKE
        pathEffect = DashPathEffect(floatArrayOf(10f, 10f), 0f)
    }

    private val axisPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#455A64")
        strokeWidth = 2f
        style = Paint.Style.STROKE
    }

    private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#90A4AE")
        textSize = 28f
    }

    private val titlePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#FFFFFF")
        textSize = 34f
        isFakeBoldText = true
    }

    private val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
    }

    fun setData(title: String, unit: String, points: List<Pair<Float, Float>>, strokeColorHex: String = "#00E5FF") {
        this.chartTitle = title
        this.unitLabel = unit
        this.dataPoints = points
        this.linePaint.color = Color.parseColor(strokeColorHex)
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        
        val width = width.toFloat()
        val height = height.toFloat()
        val paddingLeft = 100f
        val paddingRight = 40f
        val paddingTop = 70f
        val paddingBottom = 60f

        // Draw Title
        canvas.drawText(chartTitle, paddingLeft, 42f, titlePaint)

        val graphWidth = width - paddingLeft - paddingRight
        val graphHeight = height - paddingTop - paddingBottom

        if (graphWidth <= 0 || graphHeight <= 0) return

        // Draw background box
        canvas.drawRect(paddingLeft, paddingTop, paddingLeft + graphWidth, paddingTop + graphHeight, axisPaint)

        if (dataPoints.isEmpty()) {
            canvas.drawText("No Telemetry Points Available", paddingLeft + 20f, paddingTop + graphHeight / 2, textPaint)
            return
        }

        var minX = Float.MAX_VALUE
        var maxX = -Float.MAX_VALUE
        var minY = Float.MAX_VALUE
        var maxY = -Float.MAX_VALUE

        for (pt in dataPoints) {
            if (pt.first < minX) minX = pt.first
            if (pt.first > maxX) maxX = pt.first
            if (pt.second < minY) minY = pt.second
            if (pt.second > maxY) maxY = pt.second
        }

        if (maxX <= minX) maxX = minX + 1.0f
        if (maxY <= minY) {
            maxY = minY + 1.0f
            minY = Math.max(0f, minY - 0.5f)
        }

        val rangeX = maxX - minX
        val rangeY = maxY - minY

        // Draw Grid Lines (3 horizontal lines)
        for (i in 0..2) {
            val yRatio = i / 2f
            val yPos = paddingTop + graphHeight * (1f - yRatio)
            val valAtY = minY + rangeY * yRatio
            
            canvas.drawLine(paddingLeft, yPos, paddingLeft + graphWidth, yPos, gridPaint)
            canvas.drawText(String.format(Locale.US, "%.1f", valAtY), 10f, yPos + 8f, textPaint)
        }

        // Draw X-axis min/max labels
        canvas.drawText(String.format(Locale.US, "0.0 s"), paddingLeft, height - 15f, textPaint)
        canvas.drawText(String.format(Locale.US, "%.1f s", maxX), paddingLeft + graphWidth - 80f, height - 15f, textPaint)

        // Build path
        val path = Path()
        val fillPath = Path()

        var firstPoint = true
        var lastX = paddingLeft
        var lastY = paddingTop + graphHeight

        for (pt in dataPoints) {
            val normX = (pt.first - minX) / rangeX
            val normY = (pt.second - minY) / rangeY

            val xPos = paddingLeft + normX * graphWidth
            val yPos = paddingTop + graphHeight * (1f - normY)

            if (firstPoint) {
                path.moveTo(xPos, yPos)
                fillPath.moveTo(xPos, paddingTop + graphHeight)
                fillPath.lineTo(xPos, yPos)
                firstPoint = false
            } else {
                path.lineTo(xPos, yPos)
                fillPath.lineTo(xPos, yPos)
            }
            lastX = xPos
            lastY = yPos
        }

        fillPath.lineTo(lastX, paddingTop + graphHeight)
        fillPath.close()

        // Gradient Fill
        fillPaint.shader = LinearGradient(
            0f, paddingTop, 0f, paddingTop + graphHeight,
            Color.argb(70, Color.red(linePaint.color), Color.green(linePaint.color), Color.blue(linePaint.color)),
            Color.argb(0, Color.red(linePaint.color), Color.green(linePaint.color), Color.blue(linePaint.color)),
            Shader.TileMode.CLAMP
        )

        canvas.drawPath(fillPath, fillPaint)
        canvas.drawPath(path, linePaint)
    }
}
