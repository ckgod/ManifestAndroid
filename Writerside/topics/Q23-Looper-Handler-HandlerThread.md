# Q23) Looper, Handler, HandlerThread

## Looper, Handler, HandlerThread의 역할은 무엇인가요?

Looper, Handler, HandlerThread는 스레드를 관리하고 비동기 통신을 처리하기 위해 함께 작동하는 구성 요소입니다. 
이 클래스들은 백그라운드 스레드에서 작업을 수행하면서 UI 업데이트를 위해 메인 스레드와 상호 작용하는 데 필수적입니다.

![looper-handler](looper-handler.png)

### Looper

Looper는 메시지 또는 작업 큐를 순차적으로 처리하기 위해 스레드를 활성 상태로 유지하는 Android 스레딩 모델의 일부입니다. 
이는 Android의 메인 스레드 (UI thread) 및 다른 워커 스레드에서 중심적인 역할을 합니다.

*   **목적**: 메시지 큐를 지속적으로 모니터링하고, 메시지나 작업을 적절한 Handler로 가져와 전달합니다.
*   **사용법**: 메시지를 처리하는 모든 스레드에는 Looper가 필요합니다. 메인 스레드는 자동으로 Looper를 가지지만, 워커 스레드의 경우 명시적으로 준비해야 합니다.
*   **초기화**: `Looper.prepare()`를 사용하여 Looper를 스레드에 연결하고, `Looper.loop()`를 사용하여 루프를 시작합니다.

```kotlin
val thread = Thread {
    Looper.prepare() // Attach a Looper to the thread
    val handler = Handler(Looper.myLooper()!!) // Use the Looper to create a Handler
    Looper.loop() // Start the Looper
}
thread.start()
```

### Handler

Handler는 스레드의 메시지 큐 내에서 메시지 또는 작업을 보내고 처리하는 데 사용됩니다. Looper와 함께 작동합니다.
*   **목적**: 백그라운드 스레드에서 UI를 업데이트하는 것과 같이, 한 스레드에서 다른 스레드로 작업이나 메시지를 게시하는 것입니다.
*   **작동 방식**: Handler가 생성될 때, 해당 Handler는 생성된 스레드와 Looper에 연결됩니다. Handler로 전송된 작업은 해당 스레드에서 처리됩니다.

```kotlin
val handler = Handler(Looper.getMainLooper()) // Runs on the main thread

handler.post {
    // Code to update the UI
    textView.text = "Updated from background thread"
}
```

### HandlerThread

HandlerThread는 Looper가 내장된 특수 Thread입니다. 
작업 또는 메시지 큐를 처리할 수 있는 백그라운드 스레드를 생성하는 과정을 단순화합니다.

*   **목적**: 자체 Looper를 가진 워커 스레드를 생성하여, 해당 스레드에서 작업을 순차적으로 처리할 수 있도록 합니다.
*   **수명 주기**: HandlerThread를 `start()`로 시작한 다음, `getLooper()`를 사용하여 Looper를 가져옵니다. 리소스를 해제하려면 항상 `quit()` 또는 `quitSafely()`를 사용하여 Looper를 종료해야 합니다.

```kotlin
val handlerThread = HandlerThread("WorkerThread")
handlerThread.start() // Start the thread

val workerHandler = Handler(handlerThread.looper) // Use its Looper for tasks

workerHandler.post {
    // Perform background tasks
    Thread.sleep(1000)
    Log.d("HandlerThread", "Task completed")
}

// Stop the thread
handlerThread.quitSafely()
```

### 핵심 차이점 및 관계
1.  Looper는 메시지 처리의 핵심으로, 스레드를 활성 상태로 유지하고 메시지 큐를 처리합니다.
2.  Handler는 Looper와 상호 작용하여 메시지와 작업을 큐에 넣거나 처리합니다.
3.  HandlerThread는 자동 Looper 설정을 통해 백그라운드 스레드 생성을 단순화합니다.

### 사용 사례
*   Looper: 메인 스레드나 워커 스레드에서 연속적인 메시지 큐를 관리하는 데 사용됩니다.
*   Handler: 백그라운드 스레드에서 UI 업데이트를 게시하는 것과 같이, 스레드 간 통신에 적합합니다.
*   HandlerThread: 데이터 처리나 네트워크 요청과 같이 전용 스레드가 필요한 백그라운드 작업에 적합합니다.

### 요약
Looper, Handler, HandlerThread는 Android에서 스레드와 메시지 큐를 관리하기 위한 강력한 프레임워크를 형성합니다. 
Looper는 스레드가 작업을 지속적으로 처리할 수 있도록 보장하고, Handler는 작업 통신을 위한 인터페이스를 제공하며, 
HandlerThread는 내장된 메시지 루프를 사용하여 워커 스레드를 편리하게 관리하는 방법을 제공합니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Handler는 Looper와 어떻게 작동하여 스레드 간 통신을 용이하게 하며, Handler를 사용하는 일반적인 사용 사례는 무엇인가요?">

</def>
<def title="Q) HandlerThread는 무엇이며, Looper.prepare()를 사용하여 수동으로 스레드를 생성하는 것에 비해 백그라운드 스레드 관리를 어떻게 단순화하나요?">

</def>
</deflist>
