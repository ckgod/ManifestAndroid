# Details: WindowManager

## WindowManager란 무엇인가요? {#what-is-window-manager}

`WindowManager`는 화면에 표시되는 Window의 배치, 크기, 외형을 관리하는 Android 시스템 서비스입니다. 앱과 Android 시스템 사이에서 Window를 생성, 수정, 제거할 수 있는 인터페이스를 제공하며, 전체 화면 Activity부터 플로팅 오버레이까지 모든 형태의 Window를 다룹니다.

### WindowManager의 주요 역할 {#window-manager-responsibilities}

`WindowManager`는 시스템의 Window 계층 구조를 관리하는 책임을 집니다. z-order(레이어 순서)에 따라 Window가 올바르게 표시되도록 하고, 다른 시스템 Window와의 상호작용을 조율합니다. 포커스 변경, 터치 이벤트 처리, Window 애니메이션 등을 관장합니다.

### 주요 활용 사례 {#common-use-cases}

- **커스텀 View 추가**: 표준 Activity 외부에 플로팅 위젯이나 시스템 오버레이 같은 커스텀 View를 표시할 수 있습니다.
- **기존 Window 수정**: 크기 조정, 위치 변경, 투명도 조절 등 기존 Window의 속성을 업데이트할 수 있습니다.
- **Window 제거**: `removeView()` 메서드를 사용해 Window를 코드로 제거합니다.

### WindowManager 사용법 {#working-with-window-manager}

`WindowManager`는 `Context.getSystemService(Context.WINDOW_SERVICE)`를 통해 접근합니다. 아래는 `WindowManager`를 활용해 화면에 플로팅 View를 추가하는 예시입니다.

```kotlin
val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager

val floatingView = LayoutInflater.from(context).inflate(R.layout.floating_view, null)

val params = WindowManager.LayoutParams(
    WindowManager.LayoutParams.WRAP_CONTENT,
    WindowManager.LayoutParams.WRAP_CONTENT,
    WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY, // 오버레이 타입
    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,       // 포커스 비활성화
    PixelFormat.TRANSLUCENT                              // 픽셀 포맷
)

windowManager.addView(floatingView, params)
```
{title="WindowManagerExample.kt"}

- `TYPE_APPLICATION_OVERLAY`: 다른 앱 위에 View를 표시할 수 있는 타입입니다.
- `FLAG_NOT_FOCUSABLE`: 별도로 설정하지 않는 한 사용자 입력을 받지 않는 Window로 지정합니다.

### 권한 및 제한 사항 {#permissions-and-limitations}

시스템 오버레이 같은 특정 Window 타입을 사용하려면 `SYSTEM_ALERT_WINDOW` 권한이 필요합니다. Android 8.0(API 26)부터는 보안상의 이유로 오버레이 Window에 더 엄격한 제한이 적용됩니다. 사용자가 앱 설정에서 직접 권한을 허용해야 하며, 이를 반드시 사전에 확인해야 합니다.

### 요약 {#summary}

`WindowManager`는 Android에서 Window를 관리하는 핵심 API입니다. 표준 Activity 생명주기 밖에서도 View를 프로그래밍적으로 추가, 수정, 제거할 수 있어 플로팅 위젯이나 오버레이 같은 고급 기능을 구현할 수 있습니다. 다만 권한 요구 사항과 사용자 경험에 미치는 영향을 신중히 고려해야 합니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) WindowManager로 플로팅 뷰를 구현할 때 메모리 누수를 방지하는 방법은 무엇인가요?">

`WindowManager`로 추가한 View는 Activity나 Service가 종료될 때 자동으로 제거되지 않습니다. 따라서 메모리 누수를 방지하려면 다음 사항을 반드시 지켜야 합니다.

1. **Service 종료 시 제거**: Service에서 플로팅 View를 관리하는 경우, `onDestroy()`에서 반드시 `windowManager.removeView(floatingView)`를 호출합니다.
2. **null 체크**: View가 이미 제거된 상태에서 다시 `removeView()`를 호출하면 예외가 발생하므로, View의 parent가 null인지 먼저 확인합니다.
3. **Context 주의**: `windowManager`를 Activity Context로 초기화하면 Activity 종료 후에도 참조가 남아 누수가 발생할 수 있습니다. Application Context를 사용하는 것이 안전합니다.

```kotlin
override fun onDestroy() {
    super.onDestroy()
    if (floatingView.parent != null) {
        windowManager.removeView(floatingView)
    }
}
```

</def>
</deflist>
