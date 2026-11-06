package com.adshield.ui.settings;

import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.PowerManager;
import android.provider.Settings;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatDelegate;
import androidx.fragment.app.Fragment;

import com.adshield.R;
import com.adshield.data.PreferencesManager;
import com.adshield.data.model.VpnState;
import com.adshield.databinding.FragmentSettingsBinding;
import com.adshield.service.AdShieldVpnService;
import com.adshield.service.MediaAdMuteService;

public class SettingsFragment extends Fragment {

    private FragmentSettingsBinding binding;
    private PreferencesManager prefsManager;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
            @Nullable Bundle savedInstanceState) {
        binding = FragmentSettingsBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        Context context = requireContext();
        prefsManager = new PreferencesManager(context);

        setupThemePicker();
        setupDnsPicker();
        setupPrivateDnsCard();
        setupShieldSwitches();
        setupSpotifyMuteSetting();
        setupResetButton();
    }

    private void setupSpotifyMuteSetting() {
        binding.switchAutoMute.setChecked(prefsManager.isAutoMuteAdsEnabled());
        binding.switchAutoMute.setOnCheckedChangeListener((buttonView, isChecked) -> {
            prefsManager.setAutoMuteAdsEnabled(isChecked);
        });

        binding.cardNotificationAccess.setOnClickListener(v -> {
            try {
                startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS));
                Toast.makeText(requireContext(), "Turn on 'AdShield Ad Mute'", Toast.LENGTH_LONG).show();
            } catch (Exception e) {
                Toast.makeText(requireContext(), "Couldn't open the setting. Find it in Settings → Notifications → Device & app notifications.", Toast.LENGTH_LONG).show();
            }
        });
        updateNotificationAccessSummary();
    }

    private void updateNotificationAccessSummary() {
        if (getContext() == null || binding == null) return;
        if (MediaAdMuteService.isAccessGranted(requireContext())) {
            binding.tvNotificationAccessStatus.setText("On • Ads will be muted");
            binding.tvNotificationAccessStatus.setTextColor(requireContext().getColor(R.color.brand_secondary));
        } else {
            binding.tvNotificationAccessStatus.setText("Off • Tap to turn on");
            binding.tvNotificationAccessStatus.setTextColor(requireContext().getColor(R.color.status_warning));
        }
    }

    @Override
    public void onResume() {
        super.onResume();
        updateNotificationAccessSummary();
    }

    private void setupThemePicker() {
        updateThemeSummary();
        binding.cardSettingTheme.setOnClickListener(v -> {
            String[] options = {"Same as phone", "Light", "Dark"};
            int currentMode = prefsManager.getThemeMode();
            int selectedIndex = 0;
            if (currentMode == AppCompatDelegate.MODE_NIGHT_NO) {
                selectedIndex = 1;
            } else if (currentMode == AppCompatDelegate.MODE_NIGHT_YES) {
                selectedIndex = 2;
            }

            new AlertDialog.Builder(requireContext())
                    .setTitle("Theme")
                    .setSingleChoiceItems(options, selectedIndex, (dialog, which) -> {
                        int targetMode;
                        if (which == 1) {
                            targetMode = AppCompatDelegate.MODE_NIGHT_NO;
                        } else if (which == 2) {
                            targetMode = AppCompatDelegate.MODE_NIGHT_YES;
                        } else {
                            targetMode = AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM;
                        }

                        prefsManager.setThemeMode(targetMode);
                        AppCompatDelegate.setDefaultNightMode(targetMode);
                        updateThemeSummary();
                        dialog.dismiss();
                    })
                    .setNegativeButton("Cancel", null)
                    .show();
        });
    }

    private void updateThemeSummary() {
        int mode = prefsManager.getThemeMode();
        if (mode == AppCompatDelegate.MODE_NIGHT_NO) {
            binding.tvCurrentTheme.setText("Light");
        } else if (mode == AppCompatDelegate.MODE_NIGHT_YES) {
            binding.tvCurrentTheme.setText("Dark");
        } else {
            binding.tvCurrentTheme.setText("Same as phone");
        }
    }

    private void setupPrivateDnsCard() {
        if (binding.cardPrivateDnsVps == null) return;
        binding.cardPrivateDnsVps.setOnClickListener(v -> {
            new AlertDialog.Builder(requireContext())
                    .setTitle("Host Private DNS on Linux VPS")
                    .setMessage("To use Android's native Private DNS (DoT on Port 853):\n\n" +
                            "1. Deploy AdShield on your VPS using the included setup script:\n" +
                            "   bash deploy.sh\n\n" +
                            "2. On your Android phone, open:\n" +
                            "   Settings → Network & Internet → Private DNS\n\n" +
                            "3. Select 'Private DNS provider hostname' and enter your domain (e.g. dns.yourvps.com).\n\n" +
                            "Benefits: Encrypted system-wide adblocking, 0% extra battery drain, and frees up your device VPN slot!")
                    .setPositiveButton("Got it", null)
                    .show();
        });
    }

    private void setupDnsPicker() {
        updateDnsSummary();
        binding.cardSettingDns.setOnClickListener(v -> {
            String[] providers = {
                    "Cloudflare (fast, recommended)",
                    "Google",
                    "Quad9 (also blocks harmful sites)",
                    "AdGuard (blocks even more ads)",
                    "Custom AdShield VPS Server"
            };
            String[] keys = { "cloudflare", "google", "quad9", "adguard", "custom" };

            String currentKey = prefsManager.getDnsProvider();
            int selected = 0;
            for (int i = 0; i < keys.length; i++) {
                if (keys[i].equalsIgnoreCase(currentKey)) {
                    selected = i;
                    break;
                }
            }

            new AlertDialog.Builder(requireContext())
                    .setTitle("Lookup service")
                    .setSingleChoiceItems(providers, selected, (dialog, which) -> {
                        String newKey = keys[which];
                        dialog.dismiss();

                        if ("custom".equals(newKey)) {
                            promptCustomDnsDialog();
                        } else {
                            applyDnsProvider(newKey, providers[which]);
                        }
                    })
                    .setNegativeButton("Cancel", null)
                    .show();
        });
    }

    private void promptCustomDnsDialog() {
        Context ctx = requireContext();
        final android.widget.EditText input = new android.widget.EditText(ctx);
        input.setHint("VPS IP or Hostname (e.g. 1.2.3.4)");
        input.setText(prefsManager.getCustomDns());
        input.setSingleLine(true);

        int pad = (int) (18 * getResources().getDisplayMetrics().density);
        android.widget.FrameLayout container = new android.widget.FrameLayout(ctx);
        container.setPadding(pad, pad / 2, pad, 0);
        container.addView(input);

        new AlertDialog.Builder(ctx)
                .setTitle("Custom AdShield VPS IP")
                .setView(container)
                .setPositiveButton("Save", (d, w) -> {
                    String entered = input.getText().toString().trim();
                    if (!entered.isEmpty()) {
                        prefsManager.setCustomDns(entered);
                        applyDnsProvider("custom", "Custom VPS (" + entered + ")");
                    }
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void applyDnsProvider(String providerKey, String label) {
        prefsManager.setDnsProvider(providerKey);
        updateDnsSummary();

        Context ctx = requireContext();
        if (AdShieldVpnService.getVpnStateLiveData().getValue() == VpnState.CONNECTED) {
            Intent reconnectIntent = new Intent(ctx, AdShieldVpnService.class);
            reconnectIntent.setAction(AdShieldVpnService.ACTION_RECONNECT);
            ctx.startService(reconnectIntent);
        }

        Toast.makeText(ctx, "Now using " + label, Toast.LENGTH_SHORT).show();
    }

    private void updateDnsSummary() {
        String key = prefsManager.getDnsProvider();
        switch (key.toLowerCase(java.util.Locale.ROOT)) {
            case "google":
                binding.tvCurrentDns.setText("Google");
                break;
            case "quad9":
                binding.tvCurrentDns.setText("Quad9 (also blocks harmful sites)");
                break;
            case "adguard":
                binding.tvCurrentDns.setText("AdGuard (blocks even more ads)");
                break;
            case "custom":
                binding.tvCurrentDns.setText("Custom VPS (" + prefsManager.getCustomDns() + ")");
                break;
            case "cloudflare":
            default:
                binding.tvCurrentDns.setText("Cloudflare (recommended)");
                break;
        }
    }

    private void setupShieldSwitches() {
        binding.switchYoutubeShield.setChecked(prefsManager.isYouTubeProtectionEnabled());
        binding.switchYoutubeShield.setOnCheckedChangeListener((buttonView, isChecked) -> {
            prefsManager.setYouTubeProtectionEnabled(isChecked);
        });

        binding.switchSpotifyShield.setChecked(prefsManager.isSpotifyProtectionEnabled());
        binding.switchSpotifyShield.setOnCheckedChangeListener((buttonView, isChecked) -> {
            prefsManager.setSpotifyProtectionEnabled(isChecked);
        });
    }

    private void setupResetButton() {
        binding.btnResetStats.setOnClickListener(v -> {
            new AlertDialog.Builder(requireContext())
                    .setTitle("Reset counters")
                    .setMessage("Set all ad-blocking counters back to zero?")
                    .setPositiveButton("Reset", (dialog, which) -> {
                        prefsManager.resetStatistics();
                        Toast.makeText(requireContext(), "Counters reset.", Toast.LENGTH_SHORT).show();
                    })
                    .setNegativeButton("Cancel", null)
                    .show();
        });
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }
}
