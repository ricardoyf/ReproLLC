package com.ricardo.reprollc;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.provider.DocumentsContract;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.NumberPicker;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.text.DateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.Locale;
import java.util.regex.Pattern;

import androidx.media3.common.MediaItem;
import androidx.media3.common.Player;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.ui.AspectRatioFrameLayout;
import androidx.media3.ui.PlayerView;

public class MainActivity extends Activity {
    private static final int REQ_TREE = 51;
    private static final String PREFS = "reprollc_estado";
    private static final String APP_VERSION = "v1";
    private static final Pattern EDITED_TIME_RANGE = Pattern.compile(
            ".*\\d{2}\\.\\d{2}\\.\\d{2}\\.\\d{3}.*\\d{2}\\.\\d{2}\\.\\d{2}\\.\\d{3}.*");

    private final ArrayList<VideoItem> playlist = new ArrayList<>();

    private LinearLayout overlay;
    private TextView info;
    private PlayerView playerView;
    private ExoPlayer player;
    private Uri treeUri;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        buildUi();
        Uri saved = getSavedTree();
        if (saved != null) {
            treeUri = saved;
            info.setText("Carpeta anterior lista. Pulsa Fechas para reproducir fragmentos.");
        } else {
            info.setText("Elige carpeta para buscar fragmentos editados.");
        }
    }

    @Override
    protected void onDestroy() {
        releasePlayer();
        super.onDestroy();
    }

    private void buildUi() {
        android.widget.FrameLayout root = new android.widget.FrameLayout(this);
        root.setBackgroundColor(0xff000000);

        playerView = new PlayerView(this);
        playerView.setUseController(true);
        playerView.setResizeMode(AspectRatioFrameLayout.RESIZE_MODE_FIT);
        playerView.setBackgroundColor(0xff000000);
        root.addView(playerView, new android.widget.FrameLayout.LayoutParams(
                android.widget.FrameLayout.LayoutParams.MATCH_PARENT,
                android.widget.FrameLayout.LayoutParams.MATCH_PARENT));

        overlay = new LinearLayout(this);
        overlay.setOrientation(LinearLayout.VERTICAL);
        overlay.setGravity(Gravity.CENTER);
        overlay.setPadding(dp(20), dp(14), dp(20), dp(14));
        overlay.setBackgroundColor(0xcc050505);

        info = new TextView(this);
        info.setTextColor(0xffffffff);
        info.setTextSize(16);
        info.setGravity(Gravity.CENTER);
        info.setPadding(0, 0, 0, dp(12));
        overlay.addView(info, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT));

        LinearLayout buttons = new LinearLayout(this);
        buttons.setGravity(Gravity.CENTER);
        buttons.setOrientation(LinearLayout.HORIZONTAL);
        Button folder = button("Carpeta");
        Button dates = button("Fechas");
        Button stop = button("Parar");
        buttons.addView(folder);
        buttons.addView(dates);
        buttons.addView(stop);
        overlay.addView(buttons);

        TextView version = new TextView(this);
        version.setText(APP_VERSION);
        version.setTextColor(0xff9ca3af);
        version.setGravity(Gravity.CENTER);
        version.setPadding(0, dp(8), 0, 0);
        overlay.addView(version);

        android.widget.FrameLayout.LayoutParams overlayLp = new android.widget.FrameLayout.LayoutParams(
                android.widget.FrameLayout.LayoutParams.MATCH_PARENT,
                android.widget.FrameLayout.LayoutParams.WRAP_CONTENT,
                Gravity.CENTER);
        root.addView(overlay, overlayLp);
        setContentView(root);

        folder.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { pickFolder(); }
        });
        dates.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { askDateRange(); }
        });
        stop.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                releasePlayer();
                overlay.setVisibility(View.VISIBLE);
                info.setText("Reproduccion parada.");
            }
        });
        playerView.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                overlay.setVisibility(overlay.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE);
            }
        });
    }

    private Button button(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setAllCaps(false);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(120), dp(48));
        lp.setMargins(dp(5), 0, dp(5), 0);
        b.setLayoutParams(lp);
        return b;
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private void pickFolder() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
                | Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
        startActivityForResult(intent, REQ_TREE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQ_TREE && resultCode == RESULT_OK && data != null) {
            Uri uri = data.getData();
            if (uri == null) return;
            int flags = data.getFlags() & Intent.FLAG_GRANT_READ_URI_PERMISSION;
            getContentResolver().takePersistableUriPermission(uri, flags);
            getSharedPreferences(PREFS, MODE_PRIVATE).edit().putString("tree", uri.toString()).apply();
            treeUri = uri;
            info.setText("Carpeta elegida. Pulsa Fechas.");
        }
    }

    private Uri getSavedTree() {
        String raw = getSharedPreferences(PREFS, MODE_PRIVATE).getString("tree", null);
        return raw == null ? null : Uri.parse(raw);
    }

    private void askDateRange() {
        if (treeUri == null) {
            Toast.makeText(this, "Elige carpeta primero", Toast.LENGTH_SHORT).show();
            pickFolder();
            return;
        }
        Calendar today = Calendar.getInstance();
        Calendar startDefault = Calendar.getInstance();
        startDefault.add(Calendar.YEAR, -1);

        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(18), dp(8), dp(18), dp(8));
        final DateWheels start = new DateWheels("Fecha inicial", startDefault, 1990, today.get(Calendar.YEAR));
        final DateWheels end = new DateWheels("Fecha final", today, 1990, today.get(Calendar.YEAR));
        box.addView(start.view);
        box.addView(end.view);
        ScrollView scroll = new ScrollView(this);
        scroll.addView(box);

        final AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("Intervalo")
                .setView(scroll)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Reproducir", null)
                .create();
        dialog.setOnShowListener(new android.content.DialogInterface.OnShowListener() {
            @Override public void onShow(android.content.DialogInterface rawDialog) {
                dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(new View.OnClickListener() {
                    @Override public void onClick(View v) {
                        long startMs = dateMs(start, false);
                        long endMs = dateMs(end, true);
                        if (endMs < startMs) {
                            Toast.makeText(MainActivity.this, "Fecha final anterior a inicial", Toast.LENGTH_SHORT).show();
                            return;
                        }
                        dialog.dismiss();
                        loadAndPlay(startMs, endMs);
                    }
                });
            }
        });
        dialog.show();
    }

    private long dateMs(DateWheels wheels, boolean endOfDay) {
        Calendar cal = Calendar.getInstance();
        cal.set(Calendar.YEAR, wheels.year());
        cal.set(Calendar.MONTH, wheels.month() - 1);
        cal.set(Calendar.DAY_OF_MONTH, Math.min(wheels.day(), maxDay(wheels.year(), wheels.month())));
        cal.set(Calendar.HOUR_OF_DAY, endOfDay ? 23 : 0);
        cal.set(Calendar.MINUTE, endOfDay ? 59 : 0);
        cal.set(Calendar.SECOND, endOfDay ? 59 : 0);
        cal.set(Calendar.MILLISECOND, endOfDay ? 999 : 0);
        return cal.getTimeInMillis();
    }

    private void loadAndPlay(final long startMs, final long endMs) {
        info.setText("Buscando fragmentos...");
        overlay.setVisibility(View.VISIBLE);
        releasePlayer();
        new Thread(new Runnable() {
            @Override public void run() {
                final ArrayList<VideoItem> found = new ArrayList<>();
                try {
                    String rootId = DocumentsContract.getTreeDocumentId(treeUri);
                    scanFolder(rootId, found, 0, startMs, endMs);
                    sortByName(found);
                } catch (Exception e) {
                    showToast("Error buscando: " + e.getMessage());
                }
                runOnUiThread(new Runnable() {
                    @Override public void run() {
                        playlist.clear();
                        playlist.addAll(found);
                        if (playlist.isEmpty()) {
                            info.setText("No hay fragmentos editados en ese intervalo.");
                            return;
                        }
                        playList();
                    }
                });
            }
        }, "reprollc-scan").start();
    }

    private void scanFolder(String parentDocId, ArrayList<VideoItem> out, int depth, long startMs, long endMs) {
        if (depth > 20 || treeUri == null) return;
        Uri childrenUri = DocumentsContract.buildChildDocumentsUriUsingTree(treeUri, parentDocId);
        ArrayList<Doc> docs = new ArrayList<>();
        Cursor c = null;
        try {
            c = getContentResolver().query(childrenUri, new String[] {
                    DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                    DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                    DocumentsContract.Document.COLUMN_MIME_TYPE,
                    DocumentsContract.Document.COLUMN_LAST_MODIFIED
            }, null, null, DocumentsContract.Document.COLUMN_DISPLAY_NAME + " ASC");
            if (c == null) return;
            while (c.moveToNext()) {
                Doc d = new Doc();
                d.id = c.getString(0);
                d.name = c.getString(1);
                d.mime = c.getString(2);
                d.modified = c.isNull(3) ? 0L : c.getLong(3);
                if (d.id != null && d.name != null) docs.add(d);
            }
        } finally {
            if (c != null) c.close();
        }
        for (Doc d : docs) {
            if (DocumentsContract.Document.MIME_TYPE_DIR.equals(d.mime)) {
                scanFolder(d.id, out, depth + 1, startMs, endMs);
            }
        }
        for (Doc d : docs) {
            if (!isEditedVideo(d)) continue;
            if (d.modified < startMs || d.modified > endMs) continue;
            VideoItem item = new VideoItem();
            item.name = d.name;
            item.uri = DocumentsContract.buildDocumentUriUsingTree(treeUri, d.id);
            item.modified = d.modified;
            out.add(item);
        }
    }

    private boolean isEditedVideo(Doc d) {
        if (d.name == null || !EDITED_TIME_RANGE.matcher(d.name).matches()) return false;
        if (d.mime != null && d.mime.startsWith("video/")) return true;
        String n = d.name.toLowerCase(Locale.US);
        return n.endsWith(".mp4") || n.endsWith(".mov") || n.endsWith(".mkv")
                || n.endsWith(".3gp") || n.endsWith(".webm") || n.endsWith(".m4v")
                || n.endsWith(".mts") || n.endsWith(".m2ts") || n.endsWith(".avi");
    }

    private void sortByName(ArrayList<VideoItem> items) {
        Collections.sort(items, new Comparator<VideoItem>() {
            @Override public int compare(VideoItem a, VideoItem b) {
                return a.name.compareToIgnoreCase(b.name);
            }
        });
    }

    private void playList() {
        releasePlayer();
        player = new ExoPlayer.Builder(this).build();
        playerView.setPlayer(player);
        for (VideoItem item : playlist) {
            player.addMediaItem(new MediaItem.Builder().setUri(item.uri).setMediaId(item.name).build());
        }
        player.addListener(new Player.Listener() {
            @Override public void onMediaItemTransition(MediaItem mediaItem, int reason) {
                updateNowPlaying();
            }
        });
        player.prepare();
        player.play();
        overlay.setVisibility(View.GONE);
        updateNowPlaying();
    }

    private void updateNowPlaying() {
        if (player == null || playlist.isEmpty()) return;
        int current = Math.max(0, Math.min(player.getCurrentMediaItemIndex(), playlist.size() - 1));
        VideoItem item = playlist.get(current);
        DateFormat format = DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT, Locale.getDefault());
        info.setText((current + 1) + "/" + playlist.size() + "\n" + item.name
                + "\n" + (item.modified > 0 ? format.format(new Date(item.modified)) : "sin fecha"));
    }

    private void releasePlayer() {
        if (player != null) {
            try { playerView.setPlayer(null); } catch (Exception ignored) {}
            try { player.release(); } catch (Exception ignored) {}
            player = null;
        }
    }

    private void showToast(final String text) {
        runOnUiThread(new Runnable() {
            @Override public void run() {
                Toast.makeText(MainActivity.this, text, Toast.LENGTH_LONG).show();
            }
        });
    }

    private int maxDay(int year, int month) {
        Calendar cal = Calendar.getInstance();
        cal.set(Calendar.YEAR, year);
        cal.set(Calendar.MONTH, month - 1);
        return cal.getActualMaximum(Calendar.DAY_OF_MONTH);
    }

    private class DateWheels {
        final LinearLayout view;
        private final TextView title;
        private final NumberPicker yearPicker;
        private final NumberPicker monthPicker;
        private final NumberPicker dayPicker;

        DateWheels(final String label, Calendar initial, int minYear, int maxYear) {
            view = new LinearLayout(MainActivity.this);
            view.setOrientation(LinearLayout.VERTICAL);
            view.setPadding(0, dp(4), 0, dp(12));
            title = new TextView(MainActivity.this);
            title.setTextColor(0xff202020);
            title.setTextSize(15);
            view.addView(title);

            LinearLayout row = new LinearLayout(MainActivity.this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            row.setGravity(Gravity.CENTER);
            view.addView(row);
            yearPicker = addPicker(row, "Año", minYear, maxYear, initial.get(Calendar.YEAR));
            monthPicker = addPicker(row, "Mes", 1, 12, initial.get(Calendar.MONTH) + 1);
            dayPicker = addPicker(row, "Día", 1, maxDay(initial.get(Calendar.YEAR), initial.get(Calendar.MONTH) + 1), initial.get(Calendar.DAY_OF_MONTH));

            NumberPicker.OnValueChangeListener listener = new NumberPicker.OnValueChangeListener() {
                @Override public void onValueChange(NumberPicker picker, int oldVal, int newVal) {
                    clampDay();
                    refresh(label);
                }
            };
            yearPicker.setOnValueChangedListener(listener);
            monthPicker.setOnValueChangedListener(listener);
            dayPicker.setOnValueChangedListener(listener);
            clampDay();
            refresh(label);
        }

        private NumberPicker addPicker(LinearLayout parent, String label, int min, int max, int value) {
            LinearLayout column = new LinearLayout(MainActivity.this);
            column.setOrientation(LinearLayout.VERTICAL);
            column.setGravity(Gravity.CENTER);
            parent.addView(column, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            TextView text = new TextView(MainActivity.this);
            text.setText(label);
            text.setGravity(Gravity.CENTER);
            text.setTextColor(0xff444444);
            column.addView(text);
            NumberPicker picker = new NumberPicker(MainActivity.this);
            picker.setMinValue(min);
            picker.setMaxValue(max);
            picker.setValue(Math.max(min, Math.min(max, value)));
            picker.setWrapSelectorWheel(false);
            column.addView(picker, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(110)));
            return picker;
        }

        int year() { return yearPicker.getValue(); }
        int month() { return monthPicker.getValue(); }
        int day() { return dayPicker.getValue(); }

        private void clampDay() {
            int max = maxDay(year(), month());
            dayPicker.setMaxValue(max);
            if (day() > max) dayPicker.setValue(max);
        }

        private void refresh(String label) {
            title.setText(String.format(Locale.US, "%s: %04d-%02d-%02d", label, year(), month(), day()));
        }
    }

    private static class Doc {
        String id;
        String name;
        String mime;
        long modified;
    }

    private static class VideoItem {
        String name;
        Uri uri;
        long modified;
    }
}
