# Q3) Pending Intent

## PendingIntent의 목적은 무엇인가요? {#purpose-pending-intent}
PendingIntent는 다른 애플리케이션이나 시스템 컴포넌트가 애플리케이션을 대신하여 나중에 미리 정의된 인텐트를 실행할 수 있는 권한을 부여하는 특수 인텐트이다.
이는 알림, Service와의 상호작용 같이 앱 수명 외의 트리거해야 하는 작업에 유용하다.

### PendingIntent의 주요 기능 {#features-pending-intent}
PendingIntent는 일반 인텐트의 Wrapper 역할을 하여 **앱의 수명 주기 이후**에도 지속될 수 있다.
앱과 동일한 권한을 가진 다른 앱이나 시스템 서비스에 인텐트의 실행을 위임한다.
Activity, Service, BroadCast Receiver에 대해 PendingIntent를 만들 수 있다.

세 가지 주요 형태로 사용된다.
- **Activity**: Activity를 시작한다.
- **Service**: Service를 시작한다.
- **BroadCast**: BroadCast를 전송한다.

`PendingIntent.getActivity()`, `PendingIntent.getService()`, `PendingIntent.getBroadcast()`와 같은 팩토리 메서드를 사용해서 PendingIntent를 만들 수 있다.

```Kotlin
val intent = Intent(this, MyActivity::class.java)
val pendingIntent = PendingIntent.getActivity(
    this,
    0,
    intent,
    PendingIntent.FLAG_UPDATE_CURRENT
)
val notification = NotificationCompat.Builder(this, CHANNEL_ID)
    .setContentTitle("Title")
    .setContentText("Text")
    .setSmallIcon(R.drawable.ic_notification)
    .setContentIntent(pendingIntent) // 탭 했을 때 트리거된다.
    .build()
NotificationManagerCompat.from(this).notify(NOTIFICATION_ID, notification)
```

PendingIntent는 시스템 또는 다른 컴포넌트와 상호 작용하는 방식을 제어하는 다양한 플래그를 지원한다.

- **FLAG_UPDATE_CURRENT**: 기존 PendingIntent를 새 데이터로 업데이트한다.
- **FLAG_CANCEL_CURRENT**: 생성하기 전에 기존 PendingIntent를 취소한다.
- **FLAG_IMMUTABLE**: 수신자의 수정을 방지하기 위해 PendingIntent를 변경할 수 없게 만든다.
- **FLAG_ONE_SHOT**: PendingIntent를 한 번만 사용할 수 있도록 한다.

### 사용 사례
1. 알림(Notifications): 사용자가 알림을 탭하면 Activity 열기와 같은 작업을 허용
2. 알람(Alarms): AlarmManager를 사용하여 작업을 예약
3. 서비스: 백그라운드 작업을 위해 `ForegroundService` 또는 `BroadcastReceiver`에게 작업을 위임한다.

### 보안 고려 사항
악성 앱이 기본 인텐트를 수정하지 못하도록 항상 PendingIntent에 대해 `FLAG_IMMUTABLE`을 설정해야 한다.
이는 특정 시나리오에서 `FLAG_IMMUTABLE`이 필수인 안드로이드12(API 31) 이후부터 특히 중요하다.

### 요약
PendingIntent는 앱이 실행 중이 아닐 때에도 앱과 시스템 구성 요소 또는 다른 앱 간의 원활한 통신을 가능하게 하는 안드로이드의 핵심 매커니즘이다.
플래그와 권한을 신중하게 관리하면 지연된 작업을 안전하고 효율적으로 실행할 수 있다.


<deflist collapsible="true" default-state="collapsed">
<def title="Q) PendingIntent란 무엇이며 일반 Intent와 어떻게 다른가요?">

</def>
<def title="Q) PendingIntent를 사용해야 하는 시나리오를 알려주실 수 있나요?">

</def>
</deflist>