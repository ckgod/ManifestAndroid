# Q23) Looper, Handler, HandlerThread

## Looper, Handler, HandlerThread의 역할은 무엇인가요? {#looper-handler-handlerthread-roles}

Looper, Handler, HandlerThread는 스레드를 관리하고 비동기 통신을 처리하기 위해 함께 작동하는 구성 요소입니다. 
이 클래스들은 백그라운드 스레드에서 작업을 수행하면서 UI 업데이트를 위해 메인 스레드와 상호 작용하는 데 필수적입니다.

![looper-handler](looper-handler.png)

### Looper {#looper}

스레드는 기본적으로 할당된 작업을 마치면 곧바로 종료됩니다. **Looper**는 이 스레드를 종료되지 않고 계속 실행 상태로 유지하면서, 메시지 큐에 쌓인 작업을 순서대로 꺼내 처리하는 장치입니다.
Android 메인 스레드(UI 스레드)가 사용자 입력과 화면 갱신을 계속 받을 수 있는 것도 Looper 덕분입니다.

*   **목적**: 메시지 큐를 지속적으로 모니터링하고, 메시지나 작업을 적절한 Handler로 가져와 전달합니다.
*   **사용법**: 메시지를 처리하는 모든 스레드에는 Looper가 필요합니다. 메인 스레드는 자동으로 Looper를 가지지만, 워커 스레드는 명시적으로 준비해야 합니다.
*   **초기화**: `Looper.prepare()`로 Looper를 스레드에 연결하고, `Looper.loop()`로 루프를 시작합니다.

다음은 워커 스레드에서 Looper를 직접 사용하는 예시입니다.

```kotlin
val thread = Thread {
    Looper.prepare() // Attach a Looper to the thread
    val handler = Handler(Looper.myLooper()!!) // Use the Looper to create a Handler
    Looper.loop() // Start the Looper
}
thread.start()
```
{title="Looper.kt"}

### Handler {#handler}

백그라운드 스레드에서 처리한 결과를 UI에 반영하려면, 메인 스레드에서 실행되는 코드가 필요합니다. **Handler**는 Looper와 연결되어 작업이나 메시지를 특정 스레드의 메시지 큐에 전달하는 다리 역할을 합니다.

*   **목적**: 백그라운드 스레드에서 UI를 업데이트하는 것처럼, 한 스레드에서 다른 스레드로 작업이나 메시지를 전달합니다.
*   **작동 방식**: Handler가 생성될 때, 생성된 스레드와 Looper에 연결됩니다. Handler로 전송된 작업은 해당 스레드에서 처리됩니다.

다음은 메인 스레드의 Handler를 통해 UI를 업데이트하는 예시입니다.

```kotlin
// Runs on the main thread
val handler = Handler(Looper.getMainLooper())

handler.post {
    // Code to update the UI
    textView.text = "Updated from background thread"
}
```
{title="Handler.kt"}

### HandlerThread {#handlerthread}

**HandlerThread**는 Looper가 내장된 특수 Thread로, 직접 `Looper.prepare()`를 호출하지 않아도 메시지 큐를 처리할 수 있는 백그라운드 스레드를 손쉽게 생성할 수 있습니다.

*   **목적**: 자체 Looper를 가진 워커 스레드를 생성하여, 해당 스레드에서 작업을 순차적으로 처리합니다.
*   **수명 주기**: `start()`로 스레드를 시작한 뒤 `getLooper()`로 Looper를 가져옵니다. 사용이 끝나면 반드시 `quit()` 또는 `quitSafely()`로 Looper를 종료해 리소스를 해제해야 합니다.

다음은 HandlerThread를 사용하여 백그라운드 작업을 처리하는 예시입니다.

```kotlin
val handlerThread = HandlerThread("WorkerThread")
handlerThread.start() // Start the thread

// Use its Looper for tasks
val workerHandler = Handler(handlerThread.looper)

workerHandler.post {
    // Perform background tasks
    Thread.sleep(1000)
    Log.d("HandlerThread", "Task completed")
}

// Stop the thread
handlerThread.quitSafely()
```
{title="HandlerThread.kt"}

### 핵심 차이점 및 관계 {#key-differences}
1.  Looper는 메시지 처리의 핵심으로, 스레드를 활성 상태로 유지하고 메시지 큐를 처리합니다.
2.  Handler는 Looper와 상호 작용하여 메시지와 작업을 큐에 넣거나 처리합니다.
3.  HandlerThread는 자동 Looper 설정을 통해 백그라운드 스레드 생성을 단순화합니다.

### 사용 사례 {#use-cases}
*   Looper: 메인 스레드나 워커 스레드에서 연속적인 메시지 큐를 관리하는 데 사용됩니다.
*   Handler: 백그라운드 스레드에서 UI 업데이트를 게시하는 것과 같이, 스레드 간 통신에 적합합니다.
*   HandlerThread: 데이터 처리나 네트워크 요청과 같이 전용 스레드가 필요한 백그라운드 작업에 적합합니다.

### 요약 {#summary}
Looper, Handler, HandlerThread는 Android에서 스레드와 메시지 큐를 관리하기 위한 강력한 프레임워크를 형성합니다. 
Looper는 스레드가 작업을 지속적으로 처리할 수 있도록 보장하고, Handler는 작업 통신을 위한 인터페이스를 제공하며, 
HandlerThread는 내장된 메시지 루프를 사용하여 워커 스레드를 편리하게 관리하는 방법을 제공합니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Handler는 Looper와 어떻게 작동하여 스레드 간 통신을 용이하게 하며, Handler를 사용하는 일반적인 사용 사례는 무엇인가요?">

Handler는 생성 시점의 스레드와 Looper에 자동으로 연결됩니다. `handler.post { }` 또는 `handler.sendMessage()`로 전달한 작업은 해당 Looper가 실행 중인 스레드의 메시지 큐에 쌓이고, Looper가 순서대로 꺼내 실행합니다. 가장 흔한 사용 사례는 백그라운드 스레드에서 네트워크 요청이나 데이터 처리를 마친 뒤, `Handler(Looper.getMainLooper())`를 통해 메인 스레드로 결과를 전달하여 UI를 업데이트하는 것입니다. `postDelayed()`를 이용해 일정 시간 후에 실행할 작업을 예약하는 것도 자주 쓰이는 패턴입니다.

</def>
<def title="Q) HandlerThread는 무엇이며, Looper.prepare()를 사용하여 수동으로 스레드를 생성하는 것에 비해 백그라운드 스레드 관리를 어떻게 단순화하나요?">

HandlerThread는 내부적으로 `Looper.prepare()`와 `Looper.loop()` 호출을 자동으로 처리하는 전용 백그라운드 스레드입니다. 수동으로 워커 스레드를 생성하면 Looper 초기화 코드를 직접 작성해야 하고, Looper가 준비되기 전에 Handler를 생성하는 타이밍 문제도 신경 써야 합니다. 반면 HandlerThread는 `start()` 호출 후 `getLooper()`만 호출하면 바로 사용 가능하므로 코드가 훨씬 간결해집니다. 사용이 끝나면 반드시 `quitSafely()`를 호출해 Looper를 종료하고 리소스를 해제해야 합니다.

</def>
</deflist>
