# Q10) Service

## Service 란?
`Service`는 앱이 사용자 상호작용과 독립적으로 장기 실행 작업을 수행할 수 있도록 하는 백그라운드 구성 요소입니다. 
`Activity`와 달리, `Service`는 사용자 인터페이스를 가지지 않으며 앱이 포그라운드에 있지 않을 때도 계속 실행될 수 있습니다.
이들은 파일 다운로드, 음악 재생, 데이터 동기화 또는 네트워크 작업 처리와 같은 백그라운드 작업에 일반적으로 사용됩니다.

## Started Service

`startService()`를 호출하는 애플리케이션 컴포넌트에 의해 서비스가 시작됩니다. 
서비스는 `stopSelf()`를 사용하여 스스로 중지하거나 `stopService()`를 사용하여 명시적으로 중지될 때까지 백그라운드에서 무기한으로 실행됩니다.

예시 사용법:
* 백그라운드 음악 재생
* 파일 업로드 또는 다운로드

```kotlin
class MyService : Service() {
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // 백그라운드에서 장기 실행 작업 수행
        return START_STICKY
    }
    override fun onBind(intent: Intent?): IBinder? = null
}
```

## Bound Service

바운드 서비스는 컴포넌트가 `bindService()`를 사용하여 서비스에 바인딩할 수 있도록 합니다. 
서비스는 바인딩된 클라이언트가 있는 동안 활성 상태를 유지하며, 모든 클라이언트가 연결을 해제하면 자동으로 중지됩니다.

예시 사용법:
* 원격 서버에서 데이터 가져오기
* 백그라운드 Bluetooth 연결 관리


```kotlin
class BoundService : Service() {
    private val binder = LocalBinder()

    inner class LocalBinder : Binder() {
        fun getService(): BoundService = this@BoundService
    }

    override fun onBind(intent: Intent?): IBinder = binder
}
```

## Foreground Service

포그라운드 서비스는 지속적인 알림을 표시하는 동안 활성 상태를 유지하는 특별한 유형의 서비스입니다. 
음악 재생, 내비게이션 또는 위치 추적과 같이 지속적인 사용자 인식이 필요한 작업에 사용됩니다.

```kotlin
class ForegroundService : Service() {
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = createNotification()
        startForeground(1, notification)
        return START_STICKY
    }

    private fun createNotification(): Notification {
        return NotificationCompat.Builder(this, "channel_id")
                .setContentTitle("Foreground Service")
                .setContentText("Running...")
                .setSmallIcon(R.drawable.ic_notification)
                .build()
    }
}
```

## Service 유형별 주요 차이점 {#154553}

| 서비스 유형             | 백그라운드에서 실행 | 자동으로 중지                  | UI 알림 필요 |
|:-------------------|:-----------|:-------------------------|:---------|
| Started Service    | 예          | 아니요                      | 아니요      |
| Bound Service      | 예          | 예 (모든 클라이언트가 unbind 될 때) | 아니요      |
| Foreground Service | 예          | 아니요                      | 예        |


## Service 사용을 위한 모범 사례 {#461235}

* 즉시 실행할 필요가 없는 백그라운드 작업에는 서비스 대신 Jetpack WorkManager를 사용하세요. 
* 작업이 완료되면 불필요한 리소스 소모를 방지하기 위해 서비스를 중지하세요. 
* 투명성을 위해 명확한 알림을 제공하여 foreground services를 책임감 있게 사용하세요. 
* 메모리 누수를 방지하기 위해 라이프사이클 변경(서비스 라이프사이클)을 적절하게 처리하세요.

## 요약
`Service`는 사용자 상호작용 없이 백그라운드 처리를 가능하게 합니다. 
시작된 `Service`는 수동으로 중지될 때까지 실행되며, 바인딩된 `Service`는 다른 구성요소와 상호작용하고, 포그라운드 `Service`는 지속적인 알림과 함께 활성 상태를 유지합니다.
`Service`를 적절히 관리하면 효율적인 시스템 리소스 사용과 원활한 사용자 경험을 보장할 수 있습니다.

> Q) Android에서 시작된 Service와 바인딩된 Service의 차이점은 무엇이며, 각각 언제 사용해야 합니까?

#### A) {collapsible="true"}
시작된 Service와 바인드된 Service의 가장 큰 차이점은 **컴포넌트와의 상호작용 여부**와 **생명주기의 독립성**에 있습니다.

**시작된 Service(Started Service)** 는 `startService()`를 통해 호출되며, 독립적으로 백그라운드 작업을 수행하는 것이 주 목적입니다.

**생명주기**: 한 번 시작되면 호출한 컴포넌트가 사라져도 서비스 스스로 `stopSelf()`를 호출하거나 외부에서 stopService()를 호출하기 전까지는 계속 실행됩니다. 생명주기가 독립적인 것이죠.

**사용 시점**: 따라서 음악을 재생하거나 대용량 파일을 다운로드하는 것처럼, 사용자가 앱 화면을 벗어나더라도 중단 없이 작업을 완료해야 할 때 사용합니다.

반면, **바인드된 Service(Bound Service)** 는 `bindService()`를 통해 호출되며, `Activity` 같은 다른 컴포넌트와 클라이언트-서버처럼 상호작용하기 위해 사용됩니다.

**생명주기**: 생명주기가 자신에게 바인딩된 컴포넌트에 의존합니다. 즉, 서비스를 바인딩한 모든 컴포넌트가 연결을 해제하면 서비스는 자동으로 소멸됩니다.

**사용 시점**: 주로 `Activity가` 서비스의 특정 메서드를 호출하고 그 결과를 직접 받아와 UI를 갱신해야 할 때 사용합니다. 예를 들어, 실시간 위치 정보를 계속 요청해서 지도에 표시하는 경우에 적합합니다.

요약하자면, 단방향으로 작업을 지시하고 잊어버리는(fire-and-forget) 방식의 긴 작업에는 시작된 Service를, 양방향으로 데이터를 주고받는 상호작용이 필요할 때는 바인드된 Service를 선택하겠습니다. 물론, 음악 플레이어처럼 두 가지 특징이 모두 필요한 경우엔 두 방식을 함께 구현할 수도 있습니다.