# Q15) ANR

## ANR 오류의 주요 원인은 무엇이며, 이를 방지하는 방법은 무엇인가요? {#A1344}

ANR(Application Not Responding)은 앱의 main thread (UI thread)가 일반적으로 5초 이상 너무 오랫동안 차단될 때 Android에서 발생하는 오류입니다.
ANR이 발생하면 Android는 사용자에게 앱을 종료하거나 응답을 기다리도록 알림을 표시합니다.

ANR은 사용자 경험을 저하시키며 다음과 같은 다양한 요인으로 인해 발생할 수 있습니다.

* main thread에서 5초 이상 걸리는 과도한 계산 
* 장시간 실행되는 network 또는 database 작업 
* UI 작업을 차단하는 행위 (예: UI thread에서 동기적으로 실행되는 작업)

### ANR 방지 방법

ANR을 방지하려면 무겁거나 시간이 많이 소요되는 작업을 오프로드하여 main thread를 응답 가능한 상태로 유지하는 것이 중요합니다. 다음은 몇 가지 모범 사례입니다.

1. **집중적인 작업을 main thread 외부로 이동:** `file I/O`, `network requests`, `database operations`와 같은 작업을 처리하려면 `background threads` (예: `Async-Task`, `Executors`, `Thread`)를 사용하세요. 현대적이고 더 안전한 접근 방식을 위해서는 `Kotlin Coroutines`와 `Dispatchers.IO`를 활용하여 효율적인 백그라운드 작업을 관리하세요.
2. **지속적인 작업에 `WorkManager` 사용:** 데이터 동기화와 같이 백그라운드에서 실행되어야 하는 작업의 경우 `WorkManager`를 사용하세요 (이 내용은 나중에 `Category 3: Business Logic`에서 다룹니다). 이 `API`는 작업이 `main thread` 외부에서 예약되고 실행되도록 보장합니다.
3. **데이터 가져오기 최적화:** `Paging`을 구현하여 대규모 데이터 세트를 효율적으로 처리하고, `UI` 과부하를 방지하고 성능을 향상시키기 위해 데이터를 작고 관리 가능한 청크로 가져오세요.
4. **구성 변경 시 `UI` 작업 최소화:** `ViewModel`을 활용하여 `UI` 관련 데이터를 유지하고 화면 회전과 같은 구성 변경 시 불필요한 `UI` 새로 고침을 방지하세요.
5. **Android Studio로 모니터링 및 프로파일링:** `Android Studio Profiler` 도구를 활용하여 `CPU`, `memory`, `network` 사용량을 모니터링하세요. 이 도구는 `ANR`을 유발할 수 있는 성능 병목 현상을 식별하고 해결하는 데 도움이 됩니다.
6. **차단 호출 방지:** `main thread`에서 긴 루프, `sleep calls`, 동기 `network requests`와 같은 차단 작업을 방지하여 앱 성능을 원활하게 유지하세요.
7. **작은 지연에 `Handler` 사용:** `Thread.sleep()` 대신 `Handler.postDelayed()`를 사용하여 `main thread`를 차단하지 않고 작은 지연을 도입하여 반응성이 좋은 앱 경험을 제공하세요.

### 요약

ANR(Application Not Responding)은 앱의 `main thread` (`UI thread`)가 일반적으로 5초 이상 차단될 때 발생하는 Android 오류입니다.
이는 사용자 경험을 저하시키고 현재 사용자 상태를 모두 잃게 합니다.

`ANR`을 방지하려면 `network`에서 데이터를 요청하거나, `database`를 쿼리하거나, 무거운 계산 작업을 수행하는 등 집중적인 작업을 `background threads`로 이동하여 `main thread`를 가볍게 유지해야 합니다.

또한 데이터 작업을 최적화하고 [Android Studio Profiler](https://developer.android.com/studio/profile)를 사용하여 앱을 프로파일링할 수 있습니다.
더 자세한 정보는 [ANR에 대한 공식 Android 문서](https://developer.android.com/topic/performance/vitals/anr)를 참조하세요.

> Q) `ANR`을 감지 및 진단하고 앱 성능을 향상시키는 방법은 무엇인가요?