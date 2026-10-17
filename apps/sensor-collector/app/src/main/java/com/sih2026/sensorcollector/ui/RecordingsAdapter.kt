package com.sih2026.sensorcollector.ui

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.sih2026.sensorcollector.R
import com.sih2026.sensorcollector.data.RecordingSession

class RecordingsAdapter(
    private var sessions: List<RecordingSession>,
    private val onItemClick: (RecordingSession) -> Unit
) : RecyclerView.Adapter<RecordingsAdapter.ViewHolder>() {

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val tvTitle: TextView = view.findViewById(R.id.tvSessionTitle)
        val tvStatus: TextView = view.findViewById(R.id.tvSessionStatusBadge)
        val tvDate: TextView = view.findViewById(R.id.tvSessionDate)
        val tvDuration: TextView = view.findViewById(R.id.tvSessionDuration)
        val tvEvents: TextView = view.findViewById(R.id.tvSessionEvents)
        val tvSize: TextView = view.findViewById(R.id.tvSessionSize)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_recording, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val session = sessions[position]
        holder.tvTitle.text = session.folderName
        holder.tvDate.text = session.dateFormatted
        holder.tvDuration.text = String.format("Duration: %.1f s", session.durationSec)
        
        val totalImuK = session.totalImuEvents / 1000.0
        val imuStr = if (totalImuK >= 1.0) String.format("%.1fk IMU", totalImuK) else "${session.totalImuEvents} IMU"
        holder.tvEvents.text = "$imuStr | ${session.gnssCount} GNSS"
        holder.tvSize.text = session.formattedSize

        if (session.isComplete) {
            holder.tvStatus.text = "COMPLETE"
            holder.tvStatus.setTextColor(holder.itemView.context.getColor(R.color.status_ready))
        } else {
            holder.tvStatus.text = "INCOMPLETE"
            holder.tvStatus.setTextColor(holder.itemView.context.getColor(R.color.status_warning))
        }

        holder.itemView.setOnClickListener { onItemClick(session) }
    }

    override fun getItemCount(): Int = sessions.size

    fun updateData(newSessions: List<RecordingSession>) {
        this.sessions = newSessions
        notifyDataSetChanged()
    }
}
