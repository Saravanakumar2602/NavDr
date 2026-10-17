package com.sih2026.sensorcollector.ui

import android.os.Bundle
import android.os.Environment
import android.os.StatFs
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import com.sih2026.sensorcollector.R
import java.util.Locale

class SettingsFragment : Fragment() {

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        val root = inflater.inflate(R.layout.fragment_settings, container, false)

        val tvStoragePath = root.findViewById<TextView>(R.id.tvStoragePath)
        val tvStorageAvailable = root.findViewById<TextView>(R.id.tvStorageAvailable)

        val ctx = requireContext()
        val externalDir = ctx.getExternalFilesDir(null)

        if (externalDir != null) {
            tvStoragePath.text = externalDir.absolutePath

            try {
                val stat = StatFs(externalDir.path)
                val availableBytes = stat.availableBlocksLong * stat.blockSizeLong
                val availableMb = availableBytes / (1024.0 * 1024.0)
                val availableGb = availableMb / 1024.0

                val storageStr = if (availableGb >= 1.0) {
                    String.format(Locale.US, "Available Storage Space: %.2f GB", availableGb)
                } else {
                    String.format(Locale.US, "Available Storage Space: %.1f MB", availableMb)
                }
                tvStorageAvailable.text = storageStr
            } catch (e: Exception) {
                tvStorageAvailable.text = "Available Storage Space: Unknown"
            }
        }

        return root
    }
}
