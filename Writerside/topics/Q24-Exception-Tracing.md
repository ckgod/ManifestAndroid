# Q24) Exception Tracing

## 예외를 어떻게 추적하나요?

Android에서 예외를 추적하는 것은 문제를 효과적으로 진단하고 해결하는 데 중요합니다. 
Android는 문제를 식별하고 디버깅하는 데 도움이 되는 여러 도구와 기술을 제공합니다.

### Logcat을 사용한 예외 로깅

Android Studio에서 사용할 수 있는 [Logcat](https://developer.android.com/studio/debug/logcat)은 로그를 확인하고 예외를 추적하는 주요 도구입니다. 
예외가 발생하면 시스템은 예외 유형, 메시지, 그리고 예외가 발생한 코드 라인을 포함한 자세한 스택 트레이스를 Logcat에 기록합니다. 
`E/AndroidRuntime`과 같은 키워드를 사용하여 Logcat 로그를 필터링하여 예외에 집중할 수 있습니다.

### try-catch를 사용한 예외 처리

`try-catch` 블록을 사용하면 예외를 제어하여 처리하고 코드의 중요한 부분에서 앱 충돌을 방지할 수 있습니다. 예를 들어:

```kotlin
    try {
      val result = performRiskyOperation()
    } catch (e: Exception) {
      Log.e("Error", "Exception occurred: ${e.message}")
    }
```

이를 통해 예외가 로깅되어 추적하고 해결하기가 더 쉬워집니다.

### 전역 예외 핸들러 사용

`Thread.setDefaultUncaughtExceptionHandler`를 사용하여 전역 예외 핸들러를 설정하면 앱 전체에서 처리되지 않은(uncaught) 예외를 캡처하는 데 도움이 됩니다.
이는 중앙 집중식 오류 보고 또는 로깅에 특히 유용합니다.

```kotlin
    class MyApplication : Application() {
      override fun onCreate() {
        super.onCreate()
        Thread.setDefaultUncaughtExceptionHandler { thread, exception ->
          Log.e("GlobalHandler", "Uncaught exception in thread ${thread.name}: ${exception.message}")
          // Save or send the exception details
        }
      }
    }
```

이 접근 방식은 애플리케이션 전체에서 런타임 문제를 디버깅하고 모니터링하는 데 매우 효과적입니다. 
또한, 전역 예외 핸들러를 `debug` 또는 `QA builds`에서만 구현할 수 있습니다. 
이를 통해 `QA specialists`는 예외를 효율적으로 추적하고 개발팀에 자세한 보고서를 전달하여 디버깅 및 문제 해결 프로세스를 간소화할 수 있습니다.
고급 구현에 대해 자세히 알아보려면 오픈 소스 프로젝트인 [GitHub의 snitcher](https://github.com/skydoves/snitcher)를 확인해 보세요.

### Firebase Crashlytics 사용

[Firebase Crashlytics](https://firebase.google.com/docs/crashlytics)는 프로덕션 환경에서 예외를 추적하는 훌륭한 도구입니다. 
처리되지 않은 예외를 자동으로 기록하고 스택 트레이스, 디바이스 상태 및 사용자 정보를 포함한 자세한 충돌 보고서를 제공합니다. 
중요하지 않은 문제에 대해서도 사용자 지정 예외를 기록할 수 있습니다.

```kotlin
    try {
      val data = fetchData()
    } catch (e: IOException) {
      Crashlytics.logException(e)
    }
```

### Breakpoints를 사용한 디버깅

Android Studio에서 Breakpoints를 설정하면 코드 실행을 일시 중지하고 앱의 상태를 대화식으로 검사할 수 있습니다. 
이는 개발 중에 예외의 근본 원인을 식별하는 데 특히 유용합니다. 
디버그 모드를 활성화하고, Breakpoint에 도달했을 때 IDE를 사용하여 변수, 메서드 호출 및 예외 스택 트레이스를 탐색하세요.

### 버그 리포트 캡처

Android에서 버그 리포트를 캡처하면 장치 로그, 스택 트레이스 및 시스템 정보를 수집하여 문제를 진단하고 해결하는 데 도움이 됩니다.
ADB는 기본적으로 타사 솔루션을 사용하지 않고도 버그 리포트를 캡처하고 생성하는 훌륭한 방법을 제공합니다.
세 단계로 버그 리포트를 생성할 수 있습니다.

1.  **Developer Options** – 개발자 옵션을 활성화하고, **설정** > **개발자 옵션** > **버그 리포트 가져오기**로 이동하여 생성된 리포트를 공유합니다.
2.  **Android Emulator** – 확장 컨트롤을 열고 **버그 리포트**를 선택한 다음 관련 세부 정보와 함께 리포트를 저장합니다.
3.  **ADB (Android Debug Bridge)** – 터미널에서 `adb bugreport /path/to/save/bugreport`를 실행하거나, `adb -s <device_serial_number> bugreport`를 사용하여 장치를 지정합니다.

생성된 ZIP 파일에는 디버깅에 필수적인 `dumpsys`, `dumpstate`, `logcat`과 같은 로그가 포함되어 있습니다. 
버그 리포트는 액세스될 때까지 저장되며 성능 및 충돌 진단을 위해 분석될 수 있습니다. 
자세한 내용은 [공식 문서](https://developer.android.com/studio/debug/bug-report)에서 확인할 수 있습니다.

### 요약

예외 추적은 로컬 도구와 프로덕션 모니터링을 결합하여 수행됩니다. 
Logcat은 자세한 런타임 로그를 제공하며, `try-catch` 블록과 전역 예외 핸들러는 예외가 효과적으로 로깅되고 관리되도록 합니다.
Firebase Crashlytics는 프로덕션 환경에서 충돌 보고 및 디버깅을 위한 강력한 도구입니다.
Android Studio의 Breakpoints는 개발 중에 더욱 대화식인 디버깅 경험을 제공합니다. 
이러한 방법들을 함께 사용하여 포괄적인 예외 관리 및 문제 해결이 가능합니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Logcat을 사용하여 개발 환경에서 예외를 디버깅하는 것과 Firebase Crashlytics와 같은 도구를 사용하여 프로덕션 환경에서 예외를 처리하는 것의 주요 차이점은 무엇인가요? 각 경우에 이러한 예외를 어떻게 해결하나요?">

</def>
</deflist>