# Q11) BroadcastReceiver

`BroadcastReceiver`는 안드로이드 시스템이나 다른 앱에서 발생하는 특정 이벤트를 감지하고 반응할 수 있게 해주는 컴포넌트입니다.

예를 들어, 다음과 같은 상황을 감지할 수 있습니다:
- 배터리가 부족해졌을 때
- 인터넷 연결이 끊겼다가 다시 연결되었을 때
- 화면이 켜지거나 꺼졌을 때
- 앱에서 직접 만든 사용자 정의 이벤트 
- 네트워크 연결 변경 사항 모니터링.
- `SMS` 또는 전화 이벤트에 응답. 
- 충전 상태와 같은 시스템 이벤트에 대한 `UI` 업데이트. 
- 사용자 지정 브로드캐스트를 이용한 작업 또는 알람 스케줄링.

`BroadcastReceiver`를 사용하면 이런 이벤트가 발생했을 때 앱이 자동으로 반응하도록 만들 수 있습니다. 마치 "라디오 방송"처럼 시스템이나 앱이 메시지를 송출하면, 그것을 듣고 있던 `BroadcastReceiver`가 적절한 동작을 수행하는 방식입니다.

## BroadcastReceiver의 목적 {#BC1}

`BroadcastReceiver`는 `Activity`나 `Service`의 `lifecycle`에 직접 연결되지 않을 수 있는 이벤트를 처리하는 데 사용됩니다. 이는 앱이 백그라운드에서 계속 실행되지 않고도 변경 사항에 반응할 수 있도록 하는 메시징 시스템 역할을 하여 리소스를 절약합니다.

## Broadcast 유형

1.  **System Broadcast**: Android `OS`가 배터리 잔량 변경, 시간대 업데이트 또는 네트워크 연결 변경과 같은 시스템 이벤트를 앱에 알리기 위해 보냅니다.
2.  **Custom Broadcast**: 애플리케이션이 앱 내부 또는 앱 간에 특정 정보나 이벤트를 전달하기 위해 보냅니다.

## BroadcastReceiver 선언하기 {#BC2}

`BroadcastReceiver`를 생성하려면 `BroadcastReceiver` 클래스를 확장하고 `onReceive` 메서드를 재정의해야 합니다. 이 메서드에서 브로드캐스트 처리를 위한 로직을 정의합니다.

```kotlin
class MyBroadcastReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action
        if (action == Intent.ACTION_BATTERY_LOW) {
            // Handle battery low event
            Log.d("MyBroadcastReceiver", "Battery is low!")
        }
    }
}
```

## BroadcastReceiver 등록하기 {#BC3}

`BroadcastReceiver`는 두 가지 방법으로 등록할 수 있습니다.

1. **정적 등록 (Manifest를 통해)**: 앱이 실행 중이 아닐 때도 처리해야 하는 이벤트에 사용합니다. `AndroidManifest.xml` 파일에 `<intent-filter>`를 추가합니다.

```xml
<receiver android:name=".MyBroadcastReceiver">
    <intent-filter>
        <action android:name="android.intent.action.BATTERY_LOW" />
    </intent-filter>
</receiver>
```

2. **동적 등록 (코드를 통해)**: 앱이 활성 상태이거나 특정 상태일 때만 처리해야 하는 이벤트에 사용합니다.

```kotlin
val receiver = MyBroadcastReceiver()
val intentFilter = IntentFilter(Intent.ACTION_BATTERY_LOW)
registerReceiver(receiver, intentFilter)
```

## 고려 사항

*   **Lifecycle Management**: 동적 등록을 사용하는 경우, 메모리 누수를 방지하기 위해 `unregisterReceiver`를 사용하여 리시버를 등록 해제해야 합니다.
*   **Background Execution Limits**: Android 8.0 (`API` level 26)부터 백그라운드 앱은 명시적인 브로드캐스트 예외를 제외하고 브로드캐스트 수신에 제한을 받습니다. 이러한 경우를 처리하려면 `Context.registerReceiver` 또는 `JobScheduler`를 사용하세요.
*   **보안**: 민감한 정보가 포함된 브로드캐스트의 경우 무단 접근을 방지하기 위해 `permissions`으로 보호하세요.

## 요약

`BroadcastReceiver`는 특히 `OS` 시스템과 상호 작용하는 반응형 애플리케이션을 구축하는 데 필수적인 컴포넌트입니다. 이를 통해 앱은 시스템 또는 앱 이벤트를 효율적으로 수신하고 응답할 수 있습니다. `lifecycle`을 인식하는 등록 및 최신 Android 제한 사항 준수와 같은 적절한 사용은 앱이 견고하고 리소스 효율적으로 유지되도록 보장합니다.

> Q) 브로드캐스트의 유형은 무엇이며, 시스템 브로드캐스트는 기능 및 사용 측면에서 사용자 지정 브로드캐스트와 어떻게 다른가요?

