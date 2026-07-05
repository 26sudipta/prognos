# Mobile Release Checklist (M6)

Everything the app-side needs is wired; the steps below need **your** accounts/secrets and a device.
Nothing here should ever be committed — `key.properties`, `*.jks`, `*.keystore` are gitignored.

## 1. Signing (Android)

The gradle is already wired to sign with a real keystore **if `android/key.properties` exists**, and
to fall back to debug signing otherwise (so keyless builds still work).

```bash
# a) create an upload keystore (keep the passwords safe — losing them locks you out of updates)
keytool -genkey -v -keystore ~/prognos-upload.jks -keyalg RSA -keysize 2048 \
        -validity 10000 -alias prognos

# b) create android/key.properties (gitignored) with:
#    storePassword=…
#    keyPassword=…
#    keyAlias=prognos
#    storeFile=/absolute/path/to/prognos-upload.jks

# c) build the signed release
cd mobile
flutter build appbundle --release --dart-define=API_BASE_URL=https://prognos-api.onrender.com
#   → build/app/outputs/bundle/release/app-release.aab   (upload this to Play)
```

Verify the bundle is signed with your key: `jarsigner -verify -verbose -certs app-release.aab`.

## 2. Shorebird (OTA Dart patches — optional)

Lets you push Dart-only fixes without a store review. Needs a Shorebird account.

```bash
dart pub global activate shorebird_cli
shorebird login
cd mobile
shorebird init                 # generates shorebird.yaml with your app_id (commit this file)
shorebird release android --dart-define=API_BASE_URL=https://prognos-api.onrender.com
# later, to patch a shipped release without a store update:
shorebird patch android
```

Note: `shorebird release` replaces `flutter build` for store artifacts once adopted. Keep the same
`--dart-define`.

## 3. Store submission

- **Play Console:** create the app, upload the `.aab`, fill the data-safety form (see
  `docs/store_listing.md` → Privacy notes), add screenshots + feature graphic, submit for review.
- **App Store (iOS):** requires a Mac + Xcode + Apple Developer account. Set the team/bundle id in
  Xcode, archive, upload via Transporter/Xcode, fill App Privacy, submit.

## 4. Pre-submit smoke (do on a physical mid-tier Android device)

The plan's R-criteria that can only be checked on real hardware:
- Cold start ≤ ~1.5 s (release/AOT).
- A reminder fires screen-off / in Doze at `start − lead`; survives a reboot.
- The home-screen widget shows the next contest + streak and updates after a cache refresh.
- Google Sign-In completes (needs the Android OAuth client for `io.prognos.prognos` + your release
  SHA-1 registered in Google Cloud).

## OAuth clients (still outstanding from M1)

Create in the **same** Google Cloud project (Credentials → Create OAuth client ID):
- **Android** — package `io.prognos.prognos`, plus **both** the debug SHA-1 and your **release**
  keystore's SHA-1 (`keytool -list -v -keystore ~/prognos-upload.jks -alias prognos`).
- **iOS** — bundle `io.prognos.prognos`.
The existing **Web** client id stays the token audience (already configured).
