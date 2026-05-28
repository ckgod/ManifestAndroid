# Q3) Pending Intent

## PendingIntent의 목적은 무엇인가요? {#purpose-pending-intent}
PendingIntent는 다른 애플리케이션이나 시스템 컴포넌트가 애플리케이션을 대신하여 나중에 미리 정의된 인텐트를 실행할 수 있는 권한을 부여하는 특수 인텐트이다.
이는 알림, Service와의 상호작용처럼 앱의 수명 주기를 벗어나 트리거되어야 하는 작업에 유용하다.

### PendingIntent의 주요 기능 {#features-pending-intent}
PendingIntent는 일반 인텐트의 Wrapper 역할을 하여 **앱의 수명 주기 이후**에도 지속될 수 있다.
앱과 동일한 권한을 가진 다른 앱이나 시스템 서비스에 인텐트의 실행을 위임한다.
Activity, Service, Broadcast Receiver에 대해 PendingIntent를 만들 수 있다.

세 가지 주요 형태로 사용된다.
- **Activity**: Activity를 시작한다.
- **Service**: Service를 시작한다.
- **Broadcast**: Broadcast를 전송한다.

`PendingIntent.getActivity()`, `PendingIntent.getService()`, `PendingIntent.getBroadcast()`와 같은 팩토리 메서드를 사용해서 PendingIntent를 만들 수 있다.

```Kotlin
val intent = Intent(this, MyActivity::class.java)
val pendingIntent = PendingIntent.getActivity(
    this,
    0,
    intent,
    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
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
특히 안드로이드 12(API 31)부터는 `FLAG_IMMUTABLE`이나 `FLAG_MUTABLE` 중 하나를 반드시 명시해야 하며, 둘 다 지정하지 않으면 `IllegalArgumentException`이 발생한다.

### 요약
PendingIntent는 앱이 실행 중이 아닐 때에도 앱과 시스템 구성 요소 또는 다른 앱 간의 원활한 통신을 가능하게 하는 안드로이드의 핵심 메커니즘이다.
플래그와 권한을 신중하게 관리하면 지연된 작업을 안전하고 효율적으로 실행할 수 있다.


<deflist collapsible="true" default-state="collapsed">
<def title="Q) PendingIntent란 무엇이며 일반 Intent와 어떻게 다른가요?">

PendingIntent는 미리 정의해 둔 Intent의 실행 권한을 다른 앱이나 시스템에 위임하는 토큰입니다.

일반 Intent는 내가 직접 `startActivity()`, `startService()` 등을 호출해 **즉시** 실행하며, 그 실행은 내 앱의 생명주기 안에서 일어납니다. 반면 PendingIntent는 Intent 자체를 감싼 **Wrapper**로, "이 Intent를 나중에 나 대신 실행해도 된다"는 권한을 시스템에 넘기는 것이 핵심입니다.

가장 큰 차이는 **실행 주체와 시점, 그리고 권한**입니다. PendingIntent를 받은 시스템 서비스(예: NotificationManager, AlarmManager)는 내 앱이 종료된 뒤에도 **내 앱의 신원과 권한으로** 그 Intent를 실행합니다. 즉, 실행 시점은 미래로 미뤄지지만 권한은 생성한 앱의 것을 그대로 사용한다는 점이 일반 Intent와 결정적으로 다릅니다.

</def>
<def title="Q) PendingIntent를 사용해야 하는 시나리오를 알려주실 수 있나요?">

내 앱이 직접 Intent를 실행하는 것이 아니라, **다른 컴포넌트가 미래의 어느 시점에 내 앱을 대신해 작업을 실행해야 할 때** 사용합니다. 대표적인 경우는 다음과 같습니다.

- **알림(Notification)**: 사용자가 알림을 탭했을 때 특정 Activity를 열어야 하는데, 탭은 내 앱이 아니라 시스템 UI에서 발생합니다. 따라서 `setContentIntent()`에 PendingIntent를 넘겨 시스템이 대신 실행하도록 합니다.
- **알람(AlarmManager)**: 정해진 시각에 작업을 예약할 때, 그 시점에 앱이 떠 있지 않을 수 있으므로 AlarmManager에 PendingIntent를 등록합니다.
- **위젯(App Widget)**: 홈 화면 위젯의 버튼처럼 내 프로세스 밖에서 발생하는 이벤트를 내 앱의 동작과 연결할 때 사용합니다.

공통점은 모두 **트리거 주체가 내 앱 외부(시스템·런처 등)이고, 실행 시점이 즉시가 아니라는 것**입니다. 이때 보안을 위해 가능한 한 `FLAG_IMMUTABLE`을 지정해야 하며, 안드로이드 12부터는 mutability 플래그 명시가 필수입니다.

</def>
</deflist>