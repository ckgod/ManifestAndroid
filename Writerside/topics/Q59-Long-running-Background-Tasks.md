# Q59) Long-running Background Tasks 관리

## 장시간 실행되는 백그라운드 작업은 어떻게 관리하나요? {#how-to-manage-long-running-background-tasks}

Android는 장시간 실행되는 백그라운드 작업을 효율적으로 처리하기 위한 여러 메커니즘을 제공합니다. 자원 사용을 최적화하고 최신 OS의 백그라운드 실행 제약 정책을 준수하면서도 작업이 끝까지 수행되도록 보장하기 위해서입니다. 어떤 방식이 적절한지는 작업의 성격, 긴급도, 그리고 앱 수명 주기와의 상호작용에 따라 달라집니다.

### WorkManager로 영속적인 작업 처리 {#using-workmanager}

앱이 종료되거나 기기가 재부팅된 뒤에도 반드시 실행되어야 하는 작업이 있다면 [WorkManager](https://developer.android.com/topic/libraries/architecture/workmanager)가 가장 권장되는 선택지입니다. WorkManager는 백그라운드 작업을 관리하면서 네트워크 가용성, 충전 상태와 같은 제약 조건 아래에서 작업이 실행되도록 보장합니다. 로그를 업로드하거나 데이터를 동기화하는 흐름이 대표적인 사용 사례입니다.

```kotlin
class UploadWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : Worker(appContext, workerParams) {

    override fun doWork(): Result {
        // 백그라운드 작업 수행
        uploadData()
        return Result.success()
    }
}

// 작업 스케줄링
val workRequest = OneTimeWorkRequestBuilder<UploadWorker>()
    .setConstraints(
        Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()
    )
    .build()

WorkManager.getInstance(context).enqueue(workRequest)
```
{title="WorkManager.kt"}

WorkManager가 지원하는 영속 작업의 유형은 다음 세 가지입니다.

- **Immediate**: 즉시 시작해 빠르게 끝나야 하는 작업입니다. 더 높은 우선순위(expedited)로 처리할 수도 있습니다.
- **Long-running**: 10분 이상 걸릴 가능성이 있는, 상대적으로 긴 시간이 필요한 작업입니다.
- **Deferrable**: 한 번 또는 주기적으로, 나중에 실행되도록 예약된 작업입니다. 정기 실행이나 유연한 스케줄링이 필요한 경우에 적합합니다.

WorkManager는 앱 재시작이나 기기 재부팅을 가로질러도 신뢰성 있게 작업을 이어 갈 수 있도록 설계된 백그라운드 작업 스케줄러입니다. 미터링되지 않는 네트워크, idle 상태, 충분한 배터리 잔량 같은 **선언적 제약 조건(work constraints)** 을 명시할 수 있어, 적절한 환경에서만 작업이 실행되도록 만들 수 있습니다. 또한 일회성 작업과 주기적 작업 모두에 대해 견고한 스케줄링을 제공하며, 태깅(tagging)과 명명(named work)을 통한 고유 작업 교체도 지원합니다.

내부적으로는 예약된 작업을 자체 SQLite 데이터베이스에 저장하며, Doze 모드 같은 시스템 동작을 존중하도록 동작합니다. 사용자에게 중요한 짧은 작업을 위한 **expedited work** 와, 지수 백오프(exponential backoff)를 포함한 유연한 재시도 정책도 제공합니다. 복잡한 워크플로우의 경우 **work chaining** 을 통해 작업을 순차적으로 또는 병렬로 실행할 수 있고, 작업 간 데이터 전달도 자동으로 이뤄집니다.

WorkManager는 **Coroutines와 RxJava** 와도 자연스럽게 통합되어 최신 비동기 패턴에 그대로 어울립니다. 분석 데이터 업로드나 데이터 동기화처럼 장기적이고 보장 실행이 필요한 시나리오에 적합한 도구이며, 앱이 종료되면 같이 사라져도 무방한 짧은 인-프로세스 작업에는 적합하지 않습니다.

### Service로 연속 실행되는 작업 처리 {#using-services}

음악 재생이나 위치 추적처럼 연속 실행이 필요한 작업에는 **Service** 가 적합합니다. Service는 UI와 독립적으로 동작하며 앱이 백그라운드 상태일 때도 계속 실행될 수 있습니다. 사용자가 인지할 수 있어야 하는 작업이라면 영속 알림을 동반하는 **Foreground Service** 를 사용해야 합니다.

```kotlin
class MyForegroundService : Service() {
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // 장시간 실행 작업 수행
        startForeground(NOTIFICATION_ID, createNotification())
        return START_NOT_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
```
{title="MyForegroundService.kt"}

### Kotlin Coroutines와 Dispatcher 활용 {#using-coroutines}

앱 수명 주기에 묶여 있는 작업이라면 [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-overview.html)가 언어 차원의 깔끔한 구조적 접근을 제공합니다. 무거운 I/O 작업은 `Dispatchers.IO`로, CPU 집약적인 연산은 `Dispatchers.Default`로 오프로딩하는 것이 일반적인 패턴입니다. 이 방식은 앱이 종료된 뒤까지 살아남을 필요가 없는 작업에 가장 적합합니다.

```kotlin
class MyViewModel : ViewModel() {
    fun fetchData() {
        viewModelScope.launch(Dispatchers.IO) {
            val data = fetchFromNetwork()
            withContext(Dispatchers.Main) {
                updateUI(data)
            }
        }
    }
}
```
{title="CoroutinesDispatchers.kt"}

### JobScheduler로 시스템 수준 작업 처리 {#using-jobscheduler}

기기 차원의 동작이 필요하거나 충전 중 같은 특정 조건에서만 실행되어야 하는 작업이라면 **JobScheduler** 를 사용할 수 있습니다. 즉시 실행될 필요가 없는 작업에 적합합니다.

```kotlin
val jobScheduler = context.getSystemService(JobScheduler::class.java)
val jobInfo = JobInfo.Builder(JOB_ID, ComponentName(context, MyJobService::class.java))
    .setRequiredNetworkType(JobInfo.NETWORK_TYPE_UNMETERED)
    .setRequiresCharging(true)
    .build()

jobScheduler.schedule(jobInfo)
```
{title="JobScheduler.kt"}

### 요약 {#summary}

<tldr>

어떤 도구를 선택할지는 작업의 성격에 달려 있습니다. **WorkManager** 는 신뢰성 있고 영속적인 작업에, **Service** 는 미디어 재생이나 위치 추적처럼 연속 실행이 필요한 작업에, **Kotlin Coroutines** 는 수명 주기에 묶인 작업에, **JobScheduler** 는 시스템 수준의 잡(job)을 다루는 데 적합합니다. 각 도구의 성격을 이해하고 알맞게 선택·관리하는 것이 Android에서 백그라운드 작업을 효율적으로 처리하는 핵심입니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 원격 서버에서 수백 MB짜리 큰 파일을 내려받아야 하고, 앱이 종료되어도 다운로드가 계속 이어져야 하며 네트워크 환경에 따라 효율적으로 동작해야 한다면 WorkManager·Foreground Service·JobScheduler 중 어떤 메커니즘을 선택하시겠습니까?">

이 시나리오에서는 **Foreground Service** 를 중심에 두고, 필요에 따라 **WorkManager의 long-running 작업** 으로 감싸는 방식을 선택할 수 있습니다. 수백 MB의 파일 다운로드는 사용자가 명시적으로 인지할 만한 비용이 큰 작업이고, 알림으로 진행 상황을 보여 주면서 사용자에게 통제권을 제공해야 자연스럽기 때문입니다. Foreground Service는 영속 알림을 통해 작업이 진행되고 있음을 사용자에게 명확히 알릴 수 있고, 일반적인 백그라운드 실행 제약을 우회해 다운로드를 안정적으로 이어갈 수 있습니다.

다만 단순 Foreground Service만으로는 앱 프로세스가 강제 종료되거나 기기가 재부팅된 이후의 재개를 보장하기 어렵습니다. 그래서 WorkManager의 `setForegroundAsync` 또는 `setForeground`를 활용해 Foreground Service의 동작을 WorkManager 안으로 끌어들이고, long-running 작업으로 등록하는 것이 좋습니다. 이렇게 하면 앱이 종료되어도 WorkManager가 작업을 다시 큐에 띄우고 알림이 있는 Foreground Service 형태로 다운로드를 이어 갈 수 있습니다. 또한 `Constraints.Builder()`로 미터링되지 않는 네트워크에서만 실행되도록 제약을 걸어, 사용자의 모바일 데이터를 의도치 않게 소진하는 사고도 막을 수 있습니다.

JobScheduler는 시스템 수준의 잡을 다루기에는 좋지만, 즉시성과 사용자 인지 측면에서 이 작업에는 우선순위가 낮습니다. 사용자가 "지금 다운로드를 시작했다"는 사실을 알아야 하는 흐름에서는 알림이 강제되는 Foreground Service가, 그리고 그 위에서 재시도와 제약 조건을 손쉽게 다룰 수 있는 WorkManager가 더 자연스러운 조합입니다.

</def>
</deflist>
