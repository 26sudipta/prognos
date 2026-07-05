package io.prognos.prognos

import android.appwidget.AppWidgetManager
import android.content.Context
import android.content.SharedPreferences
import android.view.View
import android.widget.RemoteViews
import es.antonborri.home_widget.HomeWidgetLaunchIntent
import es.antonborri.home_widget.HomeWidgetProvider

/**
 * Home-screen widget (M6 / R7): next-or-live contest + current streak. Renders
 * only the flat values written by the Flutter side via home_widget; it never
 * reads drift. Tapping opens the app.
 */
class ContestWidgetProvider : HomeWidgetProvider() {
    override fun onUpdate(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray,
        widgetData: SharedPreferences,
    ) {
        appWidgetIds.forEach { id ->
            val views = RemoteViews(context.packageName, R.layout.contest_widget).apply {
                setTextViewText(
                    R.id.widget_title,
                    widgetData.getString("next_title", "No upcoming contests"),
                )
                val subtitle = widgetData.getString("next_subtitle", "") ?: ""
                setTextViewText(R.id.widget_subtitle, subtitle)
                setViewVisibility(
                    R.id.widget_subtitle,
                    if (subtitle.isEmpty()) View.GONE else View.VISIBLE,
                )
                setTextViewText(R.id.widget_streak, widgetData.getString("streak", "—"))

                setOnClickPendingIntent(
                    R.id.widget_root,
                    HomeWidgetLaunchIntent.getActivity(context, MainActivity::class.java),
                )
            }
            appWidgetManager.updateAppWidget(id, views)
        }
    }
}
