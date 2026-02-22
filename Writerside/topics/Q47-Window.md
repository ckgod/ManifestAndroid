# Q47) Window

## Android에서 Window란 무엇인가요? {#what-is-window}

Window는 Activity나 기타 UI 컴포넌트의 모든 View를 담는 컨테이너입니다. View 계층 구조에서 최상위 요소로서 애플리케이션 UI와 디스플레이 사이의 다리 역할을 합니다. 모든 Activity, Dialog, Toast는 각자의 Window 객체와 연결되며, 이 Window가 포함하는 View들의 레이아웃 파라미터, 애니메이션, 전환을 담당합니다.

### Window의 주요 기능 {#window-key-features}

Window 클래스는 다음과 같은 핵심 기능을 제공합니다.

1. **DecorView**: Window는 계층 구조의 루트 뷰인 `DecorView`를 포함합니다. DecorView는 일반적으로 상태 표시줄, 내비게이션 바, 앱 콘텐츠 영역을 담고 있습니다.
2. **레이아웃 파라미터**: 크기, 위치, 가시성 등의 레이아웃 파라미터를 통해 View 배치 방식을 정의하며, 코드로 동적 변경도 가능합니다.
3. **입력 처리**: 터치 제스처, 키 입력 등 입력 이벤트를 처리하고 적절한 View로 전달합니다.
4. **애니메이션과 전환**: 화면 열기, 닫기, 전환 시 애니메이션을 지원합니다.
5. **시스템 데코레이션**: 상태 표시줄, 내비게이션 바 등 시스템 UI 요소의 표시 여부를 제어할 수 있습니다.

### Window 관리 {#window-management}

Window는 `WindowManager`라는 시스템 서비스에 의해 관리됩니다. `WindowManager`는 앱 창, 시스템 다이얼로그, 알림 등 여러 Window가 기기 화면에서 올바르게 공존하고 상호작용할 수 있도록 추가, 제거, 업데이트를 담당합니다.

### 주요 활용 사례 {#common-use-cases}

**1. Activity Window 커스터마이징**

`getWindow()` 메서드로 Activity의 Window 동작을 수정할 수 있습니다. 예를 들어 상태 표시줄을 숨기거나 배경을 변경할 수 있습니다.

```kotlin
window.decorView.systemUiVisibility = View.SYSTEM_UI_FLAG_FULLSCREEN
window.setBackgroundDrawable(ColorDrawable(Color.BLACK))
```
{title="WindowCustomization.kt"}

**2. Dialog 생성**: Dialog는 전용 Window를 사용하여 구현되어, 다른 UI 요소 위에 부유할 수 있습니다.

**3. 오버레이 사용**: `TYPE_APPLICATION_OVERLAY`를 통해 시스템 레벨 기능이나 헤드업 알림 같은 오버레이 창을 만들 수 있습니다.

**4. 멀티 윈도우 모드**: Android는 분할 화면이나 화면 속 화면(PiP) 같은 멀티 윈도우 기능을 지원합니다.

### 요약 {#summary}

<tldr>
Window는 Android에서 앱의 View와 UI 요소를 담는 최상위 컨테이너입니다. Activity, Dialog, Toast 모두 각자의 Window와 연결되며, WindowManager를 통해 관리됩니다. Window를 활용하면 시스템 UI 제어, 애니메이션 적용, 오버레이 구현 등 화면 표시 방식을 세밀하게 제어할 수 있습니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 단순한 레이아웃을 가진 Activity가 화면에 표시될 때 몇 개의 Window가 존재하며, 각각 무엇인가요?">

일반적으로 Activity 하나가 표시될 때 화면에는 여러 Window가 공존합니다.

1. **앱 Window**: Activity의 UI를 담는 기본 Window입니다. `DecorView`를 루트로 갖고 있으며, 앱의 레이아웃이 여기에 배치됩니다.
2. **상태 표시줄 Window**: 시스템이 관리하는 Window로, 화면 상단의 시간, 배터리, 알림 아이콘 영역을 담당합니다.
3. **내비게이션 바 Window**: 뒤로 가기, 홈, 최근 앱 버튼(또는 제스처 영역)을 담는 시스템 Window입니다.

이 외에도 IME(소프트 키보드)가 활성화된 경우 키보드 Window가 추가되며, 상태 표시줄을 당기면 알림 패널 Window가 추가됩니다. 모든 Window는 `WindowManager`가 z-order(레이어 순서)에 따라 관리합니다.

</def>
</deflist>
