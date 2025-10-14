# Details: Service의 생명주기

이전에 학습했듯이, 서비스는 두 가지 모드로 작동할 수 있습니다:
1. Started Service: `startService()`를 사용하여 시작되며, `stopSelf()` 또는 `stopService()`를 사용하여 명시적으로 중지될 때까지 계속 실행됩니다.
2. Bound Service: `bindService()`를 사용하여 하나 이상의 컴포넌트에 연결되며, 연결되어 있는 동안 존재합니다. 수명 주기는 `onCreate()`, `onStartCommand()`, `onBind()`, `onDestroy()`와 같은 메서드를 통해 관리됩니다.

![lifecycle-service.png](lifecycle-service.png)

## Started Service의 생명주기 메서드
1.  `onCreate()`: 이 메서드는 `Service`가 처음 생성될 때 호출됩니다. `Service`에 필요한 리소스를 초기화하는 데 사용됩니다.
2.  `onStartCommand()`: `startService()`를 사용하여 `Service`가 시작될 때 트리거됩니다. 이 메서드는 실제 작업 실행을 처리하고, 반환 값(예: `START_STICKY`, `START_NOT_STICKY`)을 사용하여 `Service`가 강제 종료될 경우의 재시작 동작을 결정합니다.
3.  `onDestroy()`: `stopSelf()` 또는 `stopService()`를 사용하여 `Service`가 중지될 때 호출됩니다. 리소스 해제 또는 스레드 중지와 같은 정리 작업에 사용됩니다.

```kotlin
class SimpleStartedService : Service() {
    override fun onCreate() {
        super.onCreate()
        // Initialize resources
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // Perform long-running task
        return START_STICKY // Restart if service is killed
    }

    override fun onDestroy() {
        super.onDestroy()
        // Clean up resources
    }

    override fun onBind(intent: Intent?): IBinder? = null // Not used for started service
}
```

## Bound Service의 생명주기 메서드
1.  `onCreate()`: Started Service와 유사하게, `Service`가 생성될 때 리소스를 초기화합니다.
2.  `onBind()`: 컴포넌트가 `bindService()`를 사용하여 `Service`에 바인딩될 때 호출됩니다. 이 메서드는 `Service`에 `IBinder` 인터페이스를 제공합니다.
3.  `onUnbind()`: 마지막 클라이언트가 `Service`에서 언바인딩될 때 호출됩니다. 이 곳에서 바인딩된 클라이언트에 특화된 리소스를 정리합니다.
4.  `onDestroy()`: `Service`가 종료될 때 호출됩니다. 리소스 정리 및 진행 중인 작업 중단을 처리합니다.

```kotlin
class SimpleBoundService : Service() {
    private val binder = LocalBinder()

    override fun onCreate() {
        super.onCreate()
        // Initialize resources
    }

    override fun onBind(intent: Intent?): IBinder {
        return binder // Return the interface for the bound service
    }

    override fun onUnbind(intent: Intent?): Boolean {
        // Clean up when no clients are bound
        return super.onUnbind(intent)
    }

    override fun onDestroy() {
        super.onDestroy()
        // Clean up resources
    }

    inner class LocalBinder : Binder() {
        fun getService(): SimpleBoundService = this@SimpleBoundService
    }
}
```

## Started Service와 Bound Service 생명주기의 주요 차이점
1.  `Started Service`: 어떤 컴포넌트와도 독립적이며, 명시적으로 중지될 때까지 실행됩니다.
2.  `Bound Service`: 최소한 하나의 클라이언트에 바인딩되어 있는 동안에만 존재합니다.

## 요약
`Service` 생명주기를 이해하는 것은 효율적이고 신뢰할 수 있는 백그라운드 작업을 구현하는 데 매우 중요합니다. `Started Service`는 독립적인 작업을 수행하며 중지될 때까지 유지되는 반면, `Bound Service`는 클라이언트 상호작용을 위한 인터페이스를 제공하고 언바인딩되면 종료됩니다. 이러한 생명주기를 적절히 관리하면 최적의 리소스 활용을 보장하고 메모리 누수를 방지할 수 있습니다.