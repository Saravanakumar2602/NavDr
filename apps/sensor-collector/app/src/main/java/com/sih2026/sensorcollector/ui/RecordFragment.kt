package com.sih2026.sensorcollector.ui

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.os.Handler
import android.os.HandlerThread
import android.os.Looper
import android.os.SystemClock
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.core.app.ActivityCompat
import androidx.fragment.app.Fragment
import com.sih2026.sensorcollector.R
import org.json.JSONObject
import java.io.File
import java.io.FileWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicLong
import kotlin.math.sqrt

class RecordFragment : Fragment(), SensorEventListener, LocationListener {

    private lateinit var sensorManager: SensorManager
    private lateinit var locationManager: LocationManager

    private var accelSensor: Sensor? = null
    private var gyroSensor: Sensor? = null

    private var sensorThread: HandlerThread? = null
    private var sensorHandler: Handler? = null
    private val ioExecutor = Executors.newSingleThreadExecutor()
    private val uiHandler = Handler(Looper.getMainLooper())

    @Volatile private var isRecording = false
    private var startTimeNanos: Long = 0L

    @Volatile private var imuWriter: FileWriter? = null
    @Volatile private var gnssWriter: FileWriter? = null
    private var currentSessionDir: File? = null

    private val accelCount = AtomicLong(0)
    private val gyroCount = AtomicLong(0)
    private val gnssCount = AtomicLong(0)

    @Volatile private var lastAccelX = 0f
    @Volatile private var lastAccelY = 0f
    @Volatile private var lastAccelZ = 0f

    @Volatile private var lastGyroX = 0f
    @Volatile private var lastGyroY = 0f
    @Volatile private var lastGyroZ = 0f

    @Volatile private var gnssSpeedMps = 0f
    @Volatile private var gnssAccuracyM = 0f
    @Volatile private var gnssLat = 0.0
    @Volatile private var gnssLon = 0.0
    @Volatile private var gnssAlt = 0.0
    @Volatile private var gnssFixAvailable = false

    private lateinit var tvStatus: TextView
    private lateinit var tvDuration: TextView
    private lateinit var tvAccelValues: TextView
    private lateinit var tvAccelHz: TextView
    private lateinit var tvGyroValues: TextView
    private lateinit var tvGyroHz: TextView
    private lateinit var tvGnssStatusBadge: TextView
    private lateinit var tvGnssData: TextView
    private lateinit var tvMetricsSummary: TextView
    private lateinit var btnToggle: Button
    private lateinit var btnViewLastSession: Button

    private val uiUpdateRunnable = object : Runnable {
        override fun run() {
            if (isRecording) {
                val nowNanos = SystemClock.elapsedRealtimeNanos()
                val elapsedSec = (nowNanos - startTimeNanos) / 1e9

                val aX = lastAccelX; val aY = lastAccelY; val aZ = lastAccelZ
                val aMag = sqrt(aX * aX + aY * aY + aZ * aZ)

                val gX = lastGyroX; val gY = lastGyroY; val gZ = lastGyroZ
                val gMag = sqrt(gX * gX + gY * gY + gZ * gZ)

                val aCnt = accelCount.get()
                val gCnt = gyroCount.get()
                val gnCnt = gnssCount.get()

                val accelHz = aCnt / maxOf(0.1, elapsedSec)
                val gyroHz = gCnt / maxOf(0.1, elapsedSec)

                val approxImuBytes = (aCnt + gCnt) * 60
                val approxGnssBytes = gnCnt * 80
                val estMb = (approxImuBytes + approxGnssBytes) / (1024.0 * 1024.0)

                tvDuration.text = String.format(Locale.US, "%.1f s", elapsedSec)
                tvAccelValues.text = String.format(Locale.US, "X: %+.2f | Y: %+.2f | Z: %+.2f\nMAG: %.2f m/s²", aX, aY, aZ, aMag)
                tvAccelHz.text = String.format(Locale.US, "%.1f Hz", accelHz)

                tvGyroValues.text = String.format(Locale.US, "X: %+.3f | Y: %+.3f | Z: %+.3f\nMAG: %.3f rad/s", gX, gY, gZ, gMag)
                tvGyroHz.text = String.format(Locale.US, "%.1f Hz", gyroHz)

                tvMetricsSummary.text = String.format(
                    Locale.US,
                    "IMU Events: %d | GNSS Fixes: %d\nEst. Disk Storage: %.2f MB",
                    (aCnt + gCnt), gnCnt, estMb
                )

                val hasLocationPermission = ActivityCompat.checkSelfPermission(
                    requireContext(), Manifest.permission.ACCESS_FINE_LOCATION
                ) == PackageManager.PERMISSION_GRANTED

                if (!hasLocationPermission) {
                    tvGnssStatusBadge.text = "PERMISSION DENIED"
                    tvGnssStatusBadge.setTextColor(requireContext().getColor(R.color.status_recording))
                    tvGnssData.text = "Location permission denied.\nIMU Telemetry continues recording."
                } else if (gnssFixAvailable) {
                    tvGnssStatusBadge.text = "3D FIX ACTIVE ●"
                    tvGnssStatusBadge.setTextColor(requireContext().getColor(R.color.status_ready))
                    tvGnssData.text = String.format(
                        Locale.US,
                        "LAT: %.6f | LON: %.6f | ALT: %.1f m\nSPEED: %.2f m/s | ACCURACY: %.1f m",
                        gnssLat, gnssLon, gnssAlt, gnssSpeedMps, gnssAccuracyM
                    )
                } else {
                    tvGnssStatusBadge.text = "SEARCHING..."
                    tvGnssStatusBadge.setTextColor(requireContext().getColor(R.color.status_warning))
                    tvGnssData.text = "GNSS searching for satellite fix...\nSPEED: -- m/s | ACCURACY: -- m"
                }

                uiHandler.postDelayed(this, 150)
            }
        }
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        val root = inflater.inflate(R.layout.fragment_record, container, false)

        tvStatus = root.findViewById(R.id.tvStatus)
        tvDuration = root.findViewById(R.id.tvDuration)
        tvAccelValues = root.findViewById(R.id.tvAccelValues)
        tvAccelHz = root.findViewById(R.id.tvAccelHz)
        tvGyroValues = root.findViewById(R.id.tvGyroValues)
        tvGyroHz = root.findViewById(R.id.tvGyroHz)
        tvGnssStatusBadge = root.findViewById(R.id.tvGnssStatusBadge)
        tvGnssData = root.findViewById(R.id.tvGnssData)
        tvMetricsSummary = root.findViewById(R.id.tvMetricsSummary)
        btnToggle = root.findViewById(R.id.btnToggle)
        btnViewLastSession = root.findViewById(R.id.btnViewLastSession)

        val ctx = requireContext()
        sensorManager = ctx.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        locationManager = ctx.getSystemService(Context.LOCATION_SERVICE) as LocationManager

        accelSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        gyroSensor = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)

        btnToggle.setOnClickListener {
            if (isRecording) stopRecording() else startRecording()
        }

        btnViewLastSession.setOnClickListener {
            val dir = currentSessionDir
            if (dir != null && dir.exists()) {
                val intent = Intent(requireContext(), SessionDetailActivity::class.java).apply {
                    putExtra("EXTRA_FOLDER_PATH", dir.absolutePath)
                }
                startActivity(intent)
            }
        }

        checkLocationPermissions()
        return root
    }

    private fun checkLocationPermissions() {
        val activity = activity ?: return
        if (ActivityCompat.checkSelfPermission(activity, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(activity, arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION), 100)
        }
    }

    private fun startRecording() {
        val ctx = context ?: return
        btnViewLastSession.visibility = View.GONE

        val timestampStr = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        val dir = File(ctx.getExternalFilesDir(null), "SensorLab_$timestampStr")
        dir.mkdirs()
        currentSessionDir = dir

        val imuFile = File(dir, "imu.csv")
        val gnssFile = File(dir, "gnss.csv")
        val metaFile = File(dir, "metadata.json")

        imuWriter = FileWriter(imuFile)
        imuWriter?.write("sensor_type,timestamp_ns,sensor_time_ns,val_x,val_y,val_z\n")

        gnssWriter = FileWriter(gnssFile)
        gnssWriter?.write("timestamp_ns,elapsed_realtime_ns,latitude,longitude,altitude,speed_mps,bearing_deg,accuracy_m,bearing_accuracy_deg\n")

        val metaJson = JSONObject()
        metaJson.put("app_name", "SensorLab")
        metaJson.put("app_version", "1.0.0")
        metaJson.put("device_model", android.os.Build.MODEL)
        metaJson.put("android_version", android.os.Build.VERSION.RELEASE)
        metaJson.put("recording_start_time", timestampStr)
        metaJson.put("requested_imu_rate_hz", 200)
        metaJson.put("accel_sensor_name", accelSensor?.name ?: "Unknown")
        metaJson.put("gyro_sensor_name", gyroSensor?.name ?: "Unknown")
        metaJson.put("orientation_convention", "X=Right, Y=Up/Forward, Z=Screen Normal")
        FileWriter(metaFile).use { it.write(metaJson.toString(2)) }

        sensorThread = HandlerThread("SensorCallbackThread").apply { start() }
        sensorHandler = Handler(sensorThread!!.looper)

        startTimeNanos = SystemClock.elapsedRealtimeNanos()
        accelCount.set(0)
        gyroCount.set(0)
        gnssCount.set(0)
        isRecording = true

        accelSensor?.let { sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_FASTEST, sensorHandler) }
        gyroSensor?.let { sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_FASTEST, sensorHandler) }

        if (ActivityCompat.checkSelfPermission(ctx, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
            try {
                locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000L, 0f, this, sensorThread!!.looper)
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }

        tvStatus.text = "Status: RECORDING ACTIVE ●"
        tvStatus.setTextColor(ctx.getColor(R.color.status_recording))
        tvStatus.setBackgroundResource(R.drawable.bg_status_recording)

        btnToggle.text = getString(R.string.btn_stop_recording)
        btnToggle.setBackgroundColor(ctx.getColor(R.color.status_recording))

        uiHandler.post(uiUpdateRunnable)
    }

    private fun stopRecording() {
        val ctx = context ?: return
        isRecording = false
        uiHandler.removeCallbacks(uiUpdateRunnable)

        sensorManager.unregisterListener(this)
        try { locationManager.removeUpdates(this) } catch (e: Exception) {}

        sensorThread?.quitSafely()
        sensorThread = null
        sensorHandler = null

        val elapsedSec = (SystemClock.elapsedRealtimeNanos() - startTimeNanos) / 1e9
        val sessionDir = currentSessionDir
        val activeImuWriter = imuWriter
        val activeGnssWriter = gnssWriter

        imuWriter = null
        gnssWriter = null

        ioExecutor.execute {
            try { activeImuWriter?.flush(); activeImuWriter?.close() } catch (e: Exception) {}
            try { activeGnssWriter?.flush(); activeGnssWriter?.close() } catch (e: Exception) {}

            // Update metadata with final counts
            if (sessionDir != null && sessionDir.exists()) {
                val metaFile = File(sessionDir, "metadata.json")
                if (metaFile.exists()) {
                    try {
                        val metaJson = JSONObject(metaFile.readText())
                        metaJson.put("recording_duration_s", elapsedSec)
                        metaJson.put("total_accel_events", accelCount.get())
                        metaJson.put("total_gyro_events", gyroCount.get())
                        metaJson.put("total_gnss_events", gnssCount.get())
                        metaJson.put("actual_imu_rate_hz", accelCount.get() / maxOf(0.1, elapsedSec))
                        FileWriter(metaFile).use { it.write(metaJson.toString(2)) }
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }
                }
            }
        }

        tvStatus.text = "Status: READY ●"
        tvStatus.setTextColor(ctx.getColor(R.color.status_ready))
        tvStatus.setBackgroundResource(R.drawable.bg_status_ready)

        btnToggle.text = getString(R.string.btn_start_recording)
        btnToggle.setBackgroundColor(ctx.getColor(R.color.cyan_accent))

        if (sessionDir != null) {
            btnViewLastSession.visibility = View.VISIBLE
            Toast.makeText(ctx, "Recording saved! Tap 'INSPECT LAST RECORDING' or 'Sessions' tab.", Toast.LENGTH_LONG).show()
        }
    }

    override fun onSensorChanged(event: SensorEvent) {
        if (!isRecording) return

        val nowNanos = SystemClock.elapsedRealtimeNanos()
        val sensorTimeNanos = event.timestamp
        val isAccel = (event.sensor.type == Sensor.TYPE_ACCELEROMETER)
        val type = if (isAccel) "ACCEL" else "GYRO"

        val vX = event.values[0]
        val vY = event.values[1]
        val vZ = event.values[2]

        if (isAccel) {
            accelCount.incrementAndGet()
            lastAccelX = vX; lastAccelY = vY; lastAccelZ = vZ
        } else {
            gyroCount.incrementAndGet()
            lastGyroX = vX; lastGyroY = vY; lastGyroZ = vZ
        }

        val writer = imuWriter
        if (writer != null) {
            ioExecutor.execute {
                try {
                    writer.write("$type,$nowNanos,$sensorTimeNanos,$vX,$vY,$vZ\n")
                } catch (e: Exception) {}
            }
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    override fun onLocationChanged(location: Location) {
        if (!isRecording) return
        gnssCount.incrementAndGet()
        val nowNanos = SystemClock.elapsedRealtimeNanos()

        gnssSpeedMps = location.speed
        gnssAccuracyM = location.accuracy
        gnssLat = location.latitude
        gnssLon = location.longitude
        gnssAlt = location.altitude
        gnssFixAvailable = true

        val spd = location.speed
        val brg = location.bearing
        val acc = location.accuracy
        val brgAcc = if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) location.bearingAccuracyDegrees else 0f
        val locTimeNanos = location.elapsedRealtimeNanos

        val writer = gnssWriter
        if (writer != null) {
            ioExecutor.execute {
                try {
                    writer.write("$nowNanos,$locTimeNanos,$gnssLat,$gnssLon,$gnssAlt,$spd,$brg,$acc,$brgAcc\n")
                } catch (e: Exception) {}
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        if (isRecording) stopRecording()
    }
}
