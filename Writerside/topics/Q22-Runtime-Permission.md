# Q22) 런타임 권한

## 런타임 권한은 어떻게 처리하나요?
Android에서 런타임 권한을 처리하는 것은 원활한 사용자 경험을 보장하면서 사용자에게 민감한 데이터에 접근하는 데 필수적입니다.
Android 6.0 (API level 23)부터 앱은 설치 시 자동으로 권한을 부여받는 대신 런타임에 위험한 권한을 명시적으로 요청해야 합니다.
이 접근 방식은 사용자가 필요할 때만 권한을 부여하도록 허용하여 사용자 개인 정보 보호를 강화합니다.

### 권한 선언 및 확인
권한을 요청하기 전에 앱은 AndroidManifest.xml 파일에 권한을 선언해야 합니다.
런타임에는 권한이 필요한 기능과 사용자가 상호 작용할 때만 권한을 요청해야 합니다.
사용자에게 메시지를 표시하기 전에 `ContextCompat.checkSelfPermission()`을 사용하여 권한이 이미 부여되었는지 확인하는 것이 중요합니다.
권한이 부여되었다면 기능은 계속 진행할 수 있고, 그렇지 않다면 앱은 권한을 요청해야 합니다.

```kotlin
when {
    ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
            == PackageManager.PERMISSION_GRANTED -> {
        // 권한이 부여됨, 기능 진행
    }
    ActivityCompat.shouldShowRequestPermissionRationale(
        this, Manifest.permission.CAMERA
    ) -> {
        // 권한 요청 전에 설명 표시
        showPermissionRationale()
    }
    else -> {
        // 직접 권한 요청
        requestPermissionLauncher.launch(Manifest.permission.CAMERA)
    }
}
```

### 권한 요청
권한을 요청하는 데 권장되는 접근 방식은 권한 처리를 간소화하는 `ActivityResultLauncher` API를 사용하는 것입니다. 시스템은 사용자에게 요청을 허용하거나 거부할지 묻는 메시지를 표시합니다.

```kotlin
val requestPermissionLauncher =
    registerForActivityResult(ActivityResultContracts.RequestPermission()) { isGranted ->
        if (isGranted) {
            // 권한 부여됨, 기능 진행
        } else {
            // 권한 거부됨, 적절하게 처리
        }
    }
```
시스템은 요청을 관리하며, 사용자에게 권한을 부여하거나 거부할 수 있는 대화 상자를 제공합니다.

### 권한 설명 제공
어떤 경우에는 시스템이 `shouldShowRequestPermissionRationale()`을 사용하여 권한을 요청하기 전에 설명을 표시하도록 권장합니다.
`true`인 경우, UI는 왜 해당 권한이 필요한지 설명해야 합니다. 이는 사용자 경험을 향상시키고 권한을 얻을 가능성을 높입니다.
또한 `shouldShowRequestPermissionRationale()`이 사용자가 “다시 묻지 않음”을 선택하고 권한을 거부할 때뿐만 아니라,
앱이 새로 설치되어 아직 권한이 요청되지 않은 경우에도 `false`를 반환하여 기본적으로 `false` 상태에서 시작한다는 점을 명심해야 합니다.

```kotlin
fun showPermissionRationale() {
    AlertDialog.Builder(this)
        .setTitle("Permission Required")
        .setMessage("This feature needs access to your camera to function properly.")
        .setPositiveButton("OK") { _, _ ->
            requestPermissionLauncher.launch(Manifest.permission.CAMERA)
        }
        .setNegativeButton("Cancel", null)
        .show()
}
```

### 권한 거부 처리
사용자가 권한을 여러 번 거부하면 Android는 이를 영구적인 거부로 처리하여 앱이 해당 권한을 다시 요청하는 것을 방지할 수 있습니다.
이 경우 앱은 특정 기능이 제한되는 이유를 설명하고, 필요한 경우 사용자가 시스템 설정으로 이동하여 수동으로 권한을 부여하도록 안내해야 합니다 .
`shouldShowRequestPermissionRationale()`은 권한이 한 번도 요청되지 않았을 때와 영구적으로 거부되었을 때 모두 `false`를 반환하므로, 최소한 한 번의 요청이 이미 이루어졌는지 여부를 추적해야 합니다.

```kotlin
if (!ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.CAMERA)) {
    // 권한이 한 번도 요청되지 않았다면 요청한다.
    requestPermissions()

    // 권한이 최소 한 번 이상 요청되었다면, 앱 설정 화면으로 이동한다.
    showSettingsDialog()
}
```

```kotlin
fun showSettingsDialog() {
    val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
        data = Uri.parse("package:$packageName")
    }
    startActivity(intent)
}
```

### 위치 권한 처리
위치 권한은 포그라운드(foreground) 및 백그라운드(background) 접근으로 분류됩니다. 
포그라운드 위치 접근은 `ACCESS_FINE_LOCATION` 또는 `ACCESS_COARSE_LOCATION`을 필요로 하며, 백그라운드 접근은 `ACCESS_BACKGROUND_LOCATION`을 필요로 하는데, 이는 추가적인 정당화가 필요합니다.

```xml
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />
```

Android 10 (API level 29)부터는 백그라운드 위치를 요청하는 앱은 백그라운드 권한을 별도로 요청하기 전에 먼저 포그라운드 접근을 요청해야 합니다.

### 일회성 권한
Android 11 (API level 30)에서는 위치, 카메라, 마이크에 대한 [one-time permissions](https://developer.android.com/training/permissions/requesting#one-time)가 도입되었습니다.
사용자는 임시 접근을 부여할 수 있으며, 앱이 닫히면 해당 접근은 취소됩니다.

### 요약
런타임 권한을 올바르게 처리하는 것은 보안, 규정 준수 및 사용자 신뢰를 보장합니다.
권한 상태 확인, 설명 제공, 상황에 맞는 권한 요청, 거부 상황에 대한 적절한 처리 등 모범 사례를 따르면 개발자는 원활하고 개인 정보 보호를 고려한 사용자 경험을 만들 수 있습니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Android의 런타임 권한 시스템은 어떻게 사용자 개인 정보 보호를 향상시키며, 앱은 민감한 권한을 요청하기 전에 어떤 시나리오를 고려해야 할까요?">

</def>
</deflist>