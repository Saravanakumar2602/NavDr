package com.sih2026.sensorcollector

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.sih2026.sensorcollector.ui.HistoryFragment
import com.sih2026.sensorcollector.ui.RecordFragment
import com.sih2026.sensorcollector.ui.SettingsFragment

class MainActivity : AppCompatActivity() {

    private val recordFragment = RecordFragment()
    private val historyFragment = HistoryFragment()
    private val settingsFragment = SettingsFragment()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val bottomNav = findViewById<BottomNavigationView>(R.id.bottomNav)

        // Default tab: Record Dashboard
        loadFragment(recordFragment)

        bottomNav.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_record -> {
                    loadFragment(recordFragment)
                    true
                }
                R.id.nav_history -> {
                    val newHistoryFragment = HistoryFragment()
                    loadFragment(newHistoryFragment)
                    true
                }
                R.id.nav_settings -> {
                    loadFragment(settingsFragment)
                    true
                }
                else -> false
            }
        }
    }

    private fun loadFragment(fragment: Fragment) {
        supportFragmentManager.beginTransaction()
            .replace(R.id.fragmentContainer, fragment)
            .commit()
    }
}
