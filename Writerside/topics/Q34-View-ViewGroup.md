# Q34) View, ViewGroup

## View와 ViewGroup의 차이점은 무엇인가요? {#VV1}

View와 ViewGroup은 UI 컴포넌트를 구현하는 데 있어 핵심적인 개념입니다.
둘 모두 `android.view` 패키지에 속하지만, UI 계층 구조에서 서로 다른 목적을 가집니다.

### View란 무엇인가요?

View는 화면에 표시되는 단일의 직사각형 UI 요소입니다.
이는 `Button`, `TextView`, `ImageView`, `EditText`와 같은 모든 UI 컴포넌트의 기본 클래스입니다.
각 View는 화면에 그리기 및 터치 또는 키 이벤트와 같은 사용자 상호작용을 처리합니다.

```kotlin
val textView = TextView(context).apply {
    text = "Hello, World!"
    textSize = 16f
    setTextColor(Color.BLACK)
}
```

> View 시스템은 Android 개발의 핵심 기반 중 하나이며, 전체 UI 프레임워크의 중추 역할을 합니다. 이는 UI 컴포넌트 렌더링 및 업데이트, 그리고 사용자 상호작용을 가능하게 하는 콜백 시스템 관리를 담당합니다. 기본적인 버튼부터 복잡한 레이아웃에 이르기까지 모든 UI 요소는 `View` 클래스를 기반으로 구축됩니다.
>
> `AOSP`에 있는 [View.java](https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/view/View.java)의 내부 구현을 살펴보면 34,000줄이 넘는 코드로 이루어져 있음을 알 수 있습니다. 이러한 복잡성은 `View` 인스턴스를 생성하고 관리하는 데 상당한 처리 오버헤드가 수반된다는 점을 강조합니다. 결과적으로, 불필요한 `View` 생성은 애플리케이션의 성능에 영향을 미쳐 메모리 사용량을 늘리고 렌더링 속도를 저하시킬 수 있습니다.
>
> 성능 최적화를 위해서는 가능한 한 불필요한 `View` 인스턴스 생성을 피해야 합니다. 또한, 레이아웃 트리의 깊이를 줄이는 것이 중요합니다. 깊게 중첩된 `View`는 측정(measure), 레이아웃(layout), 그리기(draw) 시간 증가로 이어질 수 있기 때문입니다. UI 계층 구조를 얕고 효율적으로 유지하면 더 부드러운 성능, 향상된 응답성, 낮은 리소스 소비를 보장합니다.

### ViewGroup이란 무엇인가요?

`ViewGroup`은 여러 `View` 또는 다른 `ViewGroup` 요소를 포함하는 컨테이너입니다.
이는 `LinearLayout`, `RelativeLayout`, `ConstraintLayout`, `FrameLayout`과 같은 레이아웃의 기본 클래스입니다.
`ViewGroup`은 자식 `View`들의 레이아웃 및 위치 지정을 관리하며, 이들이 화면에 어떻게 측정되고 그려지는지를 정의합니다.

```kotlin
val linearLayout = LinearLayout(context).apply {
    orientation = LinearLayout.VERTICAL
    addView(TextView(context).apply { text = "Child 1" })
    addView(TextView(context).apply { text = "Child 2" })
}
```

> `ViewGroup` 클래스는 `View`를 확장하고 `ViewParent` 및 `ViewManager` 인터페이스를 모두 구현합니다. `ViewGroup`은 다른 `View` 객체들을 위한 컨테이너 역할을 하므로, 독립적인 `View`보다 본질적으로 더 복잡하고 리소스 집약적입니다. `LinearLayout`, `RelativeLayout`, `ConstraintLayout`과 같은 레이아웃은 모두 `ViewGroup` 구현의 예시이며, `ViewGroup` 인스턴스의 과도한 중첩은 렌더링 성능에 부정적인 영향을 미칠 수 있습니다.
>
> `ViewParent` 인터페이스는 `View` 객체의 부모 역할을 하는 클래스의 책임(레이아웃 측정, 터치 이벤트 처리, 그리기 순서 관리)을 정의합니다. 반면에 `ViewManager` 인터페이스는 `ViewGroup` 계층 구조 내에서 자식 `View`를 동적으로 추가하고 제거하는 메서드를 제공합니다. `ViewGroup`은 추가적인 레이아웃 계산을 수행하고 여러 자식 `View`를 관리해야 하므로, 불필요한 중첩을 줄이는 것이 성능 최적화 및 원활한 UI 렌더링을 위해 필수적입니다.

### View와 ViewGroup의 주요 차이점

1.  **목적**
   * `View`는 콘텐츠를 표시하거나 사용자와 상호작용하도록 설계된 단일 UI 요소입니다.
   * `ViewGroup`은 여러 자식 `View`를 구성하고 관리하기 위한 컨테이너입니다.
2.  **계층 구조**
   * `View`는 UI 계층 구조에서 리프 노드(leaf node)입니다. 다른 `View`를 포함할 수 없습니다.
   * `ViewGroup`은 여러 자식 `View` 또는 다른 `ViewGroup` 요소를 포함할 수 있는 브랜치 노드(branch node)입니다.
3.  **레이아웃 동작**
    * `View`는 Layout Params에 의해 정의된 자체 크기와 위치를 가집니다.
    * `ViewGroup`은 `LinearLayout` 또는 `ConstraintLayout`과 같은 특정 레이아웃 규칙을 사용하여 자식 `View`의 크기와 위치를 정의합니다.
4.  **상호작용 처리**
    * `View`는 자체 터치 및 키 이벤트를 처리합니다.
    * `ViewGroup`은 `onInterceptTouchEvent`와 같은 메서드를 사용하여 자식에 대한 이벤트를 가로채고 관리할 수 있습니다.
5.  **성능 고려 사항**
    * `ViewGroup`은 계층적 구조로 인해 렌더링에 복잡성을 더합니다. 중첩된 `ViewGroup`을 과도하게 사용하면 렌더링 시간 증가 및 UI 업데이트 지연과 같은 성능 문제로 이어질 수 있습니다.

### 요약

`View`는 모든 UI 요소의 기반이며, `ViewGroup`은 여러 `View` 객체를 구성하고 관리하기 위한 컨테이너 역할을 합니다.
이 둘은 함께 복잡한 Android 사용자 인터페이스를 구축하기 위한 빌딩 블록을 형성합니다.
이들의 역할과 차이점을 이해하는 것은 레이아웃을 최적화하고 반응성이 뛰어난 사용자 경험을 보장하는 데 필수적입니다.

#### Q1
> `View` 라이프사이클에서 `requestLayout()`, `invalidate()`, `postInvalidate()`가 어떻게 작동하며, 각각을 언제 사용해야 하는지 설명하세요.

##### A {collapsible="true"}
이 세 가지 메서드는 어떤 스레드에서 호출하는지와 View 라이프사이클의 어느 단계(Measure, Layout, Draw)를 다시 실행하는지에 따라 명확히 구분됩니다.

1. **`invalidate()`**
   * 모양은 바뀌었지만, 크기는 그대로일 때
   * View가 다시 그려져야 함을 시스템에 알립니다. 
   * `onMeasure`, `onLayout` 과정을 생략하고, 바로 `onDraw` 단계만 실행합니다.
   * 뷰의 크기나 위치는 변하지 않고, 내부의 시각적 요소만 변경될 때 호출합니다. 
   * 반드시 ui 스레드에서만 호출해야 합니다. 
   * 텍스트 색상 변경, 배경색 변경, 터치 인터랙션에 따른 하이라이트 효과 등
2. **`postInvalidate()`**
   * 백그라운드 스레드에서 다시 그려야 할 때
   * 기능적으로 `invalidate`와 완전히 동일합니다. (결국 `onDraw()` 호출) 
   * 단, 내부적으로 `Handler`를 사용하여 UI 스레드의 메시지 큐에 `invalidate()` 요청을 전달하는 방식입니다. 
   * 백그라운드 스레드에서 호출 가능합니다. 
   * 별도의 작업 스레드에서 다운로드 진행률을 갱신할 때
   * 타이머나 네트워크 응답에 따라 UI를 갱신해야 하는데, 해당 로직이 메인 스레드가 아닐 때
3. **`requestLayout()`**
   * 크기나 위치가 바뀌어 전체 계산이 필요할 때
   * View의 크기(Measure)나 위치(Layout)가 변경되었음을 시스템에 알립니다. 
   * View 트리 구조를 타고 올라가 `ViewRootImpl`까지 요청이 전달되며, 전체 트리에 대해 `onMeasure` -> `onLayout` -> `onDraw` 과정을 순차적으로 다시 수행합니다. 
   * 비용이 가장 많이 드는 작업이므로 남용하지 않아야 합니다. 
   * UI 스레드에서 호출해야 합니다. 
   * View의 데이터가 바뀌어 크기가 변경되었을 때
   * View를 추가하거나 제거할 때
   * View의 `LayoutParams`를 변경했을 때

#### Q2
> `View` 라이프사이클은 `Activity` 라이프사이클과 어떻게 다르며, 효율적인 UI 렌더링을 위해 둘 모두를 이해하는 것이 중요한 이유는 무엇인가요?

##### A {collapsible="true" #A2}

| 구분        | Activity Lifecycle                                    | View Lifecycle                                               |
|-----------|-------------------------------------------------------|--------------------------------------------------------------|
| **관점**    | 시스템 관점 (OS Level)                                     | 화면 그리기 관점 (Rendering Level)                                  |
| **역활**    | 앱의 화면(Window)을 생성하고, 사용자와 상호작용하는 진입점이자 컨테이너입니다.       | 컨테이너 내부에서 실제로 보여지는 **UI 구성 요소(Widget)**의 크기, 위치, 그리기를 담당합니다. |
| **주요 상태** | Created, Started, Resumed, Paused, Stopped, Destroyed | Constructor, Attached, Measure, Layout, Draw, Detached       |
| **핵심 질문** | "지금 이 화면이 사용자에게 보이는가?"                                | "이 UI 요소를 어떻게, 어디에 그릴 것인가?"                                  |

View는 독자적으로 존재할 수 없으며, 반드시 Activity(또는 Fragment)라는 호스트 내부에 존재합니다. 
따라서 Activity의 상태 변화가 View의 라이프사이클을 트리거합니다. 

1. Activity `onCreate()`: View 객체가 생성되고, XML이 인플레이트됩니다.
2. Activity `onResume()`: 화면이 사용자에게 보이기 직전입니다. 이 시점에 View는 `onAttachedToWindow()`가 호출되며 윈도우에 붙습니다. 
3. 렌더링 시작: Activity가 활성화되면 View 시스템이 `measure()`, `layout()`, `draw()` 를 수행하여 화면을 그립니다.
4. Activity `onPause()` / `onStop()`: 화면이 가려집니다. 이 때 View는 애니메이션을 중지하거나 리소스를 해제해야 합니다. 
5. Activity `onDestroy()`: Activity가 종료되면 View는 `onDetachedFromWindow()` 를 호출하며 윈도우에서 떨어져 나갑니다.

**효율적인 UI렌더링을 위해 둘 모두를 이해해야 하는 이유**

Activity의 상태에 맞춰 View의 그리기 작업을 동기화하여 리소스 낭비와 오류를 막기 위함입니다. 

1. 불필요한 렌더링 연산을 방지 
   * Activity가 onStop() 상태가 되어 화면이 사용자에게 보이지 않게 되면, View 역시 애니메이션이나 invalidate() 호출을 멈춰야 합니다.
   * 만일 Activity의 라이프사이클을 무시하고 백그라운드에서도 View가 계속 그려진다면, CPU와 GPU 자원을 낭비하고 배터리 소모를 야기하게 됩니다.
2. 메모리 누수 방지
   * View는 생성 시 Context로 Activity를 참조합니다. Activity가 onDestroy() 되어 종료되었는데도, View 내부의 핸들러나 비동기 작업이 View를 계속 참조하고 있다면, Activity 전체가 GC되지 못하는 심각한 메모리 누수가 발생합니다. 따라서 Activity 종료 시점에 맞춰 View의 리스너나 작업을 해제해 주는 것이 중요합니다. 
