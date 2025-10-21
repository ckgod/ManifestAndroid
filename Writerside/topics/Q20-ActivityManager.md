# Q20) ActivityManager

## ActivityManager는 무엇인가요? {#454}

`ActivityManager`는 Android에서 실행 중인 액티비티, 태스크, 프로세스에 대한 정보를 제공하고 이를 관리하는 시스템 서비스입니다. 이는 Android 프레임워크의 일부로, 개발자가 앱 `lifecycle`, 메모리 사용량 및 태스크 관리 측면과 상호 작용하고 제어할 수 있도록 합니다. `ActivityManager`의 주요 기능은 다음과 같습니다:

1.  **태스크 및 액티비티 정보**: `ActivityManager`는 실행 중인 태스크, 액티비티 및 해당 스택 상태에 대한 세부 정보를 검색할 수 있습니다. 이는 개발자가 앱 동작 및 시스템 리소스 사용량을 모니터링하는 데 도움이 됩니다.
2.  **메모리 관리**: 시스템 전반의 메모리 사용량에 대한 정보를 제공하며, 여기에는 앱별 메모리 소비와 시스템 전체 메모리 상태가 포함됩니다. 개발자는 이를 사용하여 앱 성능을 최적화하고 `low-memory` 조건을 처리할 수 있습니다.
3.  **앱 프로세스 관리**: `ActivityManager`를 사용하면 실행 중인 앱 `processes` 및 서비스에 대한 세부 정보를 쿼리할 수 있습니다. 개발자는 이 정보를 사용하여 앱 상태를 감지하거나 프로세스 수준 변경 사항에 응답할 수 있습니다.
4.  **디버깅 및 진단**: `heap dumps` 생성 또는 앱 프로파일링과 같은 디버깅 도구를 제공하여 성능 병목 현상이나 메모리 누수를 식별하는 데 도움이 될 수 있습니다.

### `ActivityManager`의 일반적인 메서드

*   `getRunningAppProcesses()`: 현재 기기에서 실행 중인 `processes` 목록을 반환합니다.
*   `getMemoryInfo(ActivityManager.MemoryInfo memoryInfo)`: 가용 메모리, `threshold memory`, 기기가 `low-memory state`인지 여부와 같은 시스템에 대한 자세한 메모리 정보를 검색합니다. 이는 `low-memory` 조건에서 앱 동작을 최적화하는 데 유용합니다.
*   `killBackgroundProcesses(String packageName)`: 이 메서드는 지정된 앱의 백그라운드 `processes`를 종료하여 시스템 리소스를 확보합니다. 리소스 집약적인 앱을 테스트하거나 관리하는 데 유용합니다.
*   `isLowRamDevice()`: 기기가 `low-RAM`으로 분류되는지 확인하여 앱이 `low-memory` 기기에 대한 리소스 사용량을 최적화하도록 돕습니다.
*   `appNotResponding(String message)`: 이 메서드는 테스트 목적으로 `App Not Responding (ANR)` 이벤트를 시뮬레이션합니다. 디버깅 중에 `ANR` 상황에서 앱이 어떻게 동작하거나 응답하는지 이해하는 데 사용될 수 있습니다.
*   `clearApplicationUserData()`: 이 메서드는 파일, 데이터베이스 및 `shared preferences`를 포함하여 애플리케이션과 관련된 모든 사용자별 데이터를 지웁니다. 공장 초기화 또는 앱을 기본 상태로 재설정하는 경우에 자주 사용됩니다.

### 예시 사용법

다음 코드는 `ActivityManager`를 사용하여 메모리 정보를 가져오는 방법을 보여줍니다:

```kotlin
    val activityManager = getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
    val memoryInfo = ActivityManager.MemoryInfo()
    activityManager.getMemoryInfo(memoryInfo)
    
    Log.d(TAG, "Low memory state: ${memoryInfo.lowMemory}")
    Log.d(TAG, "Threshold memory: ${memoryInfo.threshold / (1024 * 1024)} MB")
    Log.d(TAG, "Threshold memory: ${memoryInfo.threshold / (1024 * 1024)} MB")
    
    val processes = activityManager.runningAppProcesses
    Log.d(TAG, "Process name: ${processes.first().processName}")
    
    // 앱이 멈췄고 ANR을 발생시키고 싶다고 시스템에 알리는 메서드입니다.
    activityManager.appNotResponding("Pokedex is not responding")
    
    // 애플리케이션이 디스크에서 자체 데이터를 지울 수 있도록 허용합니다.
    activityManager.clearApplicationUserData()
```

### `LeakCanary`에서의 `ActivityManager`

[LeakCanary](https://square.github.io/leakcanary/)는 `Block`이 유지 관리하는 Android 애플리케이션을 위한 오픈 소스 메모리 누수 감지 라이브러리입니다. 개발 중에 앱의 메모리 누수를 자동으로 모니터링하고 감지하여 누수를 효율적으로 수정하는 데 도움이 되는 상세한 분석 및 실행 가능한 통찰력을 제공합니다. [이는 메모리 상태 및 정보를 추적하기 위해 `ActivityManager`를 활용합니다.](https://github.com/square/leakcanary/blob/02d0d8b6ebfe8de55c109b904d7b526063f3f852/leakcanary/leakcanary-android-process/src/main/java/leakcanary/LeakCanaryProcess.kt#L75)

### 요약

`ActivityManager`는 시스템 수준 관리, 성능 튜닝 및 앱 동작 모니터링을 위한 것입니다. 최신 Android에서는 해당 기능이 더 전문화된 `API`에 의해 부분적으로 대체되었지만, Android 애플리케이션에서 리소스 사용량을 관리하고 최적화하는 데 여전히 유용한 도구입니다. 개발자는 의도치 않은 시스템 성능 영향 없이 이를 책임감 있게 사용할 수 있습니다.

> Q) `ActivityManager.getMemoryInfo()`는 앱 성능을 최적화하는 데 어떻게 사용될 수 있으며, 시스템이 `low-memory state`에 진입할 때 개발자는 어떤 조치를 취해야 합니까?
