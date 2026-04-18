# Q7) Composition

## Composition은 무엇이며 어떻게 생성하나요? {#what-is-composition}

[Composition](https://developer.android.com/develop/ui/compose/lifecycle#composition-anatomy)은 앱의 UI를 표현하는 단위로, 컴포저블 함수의 실행 결과로 만들어집니다. UI를 컴포저블의 트리 구조로 조직하고, **Composer** 를 통해 이 트리를 동적으로 생성·관리합니다. Composition은 상태를 기록하고, 노드 트리에 필요한 변경을 적용해 UI를 효율적으로 갱신하는 일을 담당하는데, 이 과정이 바로 **리컴포지션** 입니다. 다시 말해 Composition은 Jetpack Compose의 척추에 해당하며, 런타임에 UI 구조와 컴포저블 함수의 상태를 함께 관리합니다.

### Composition을 만드는 방법 {#creating-a-composition}

**Composition** 은 컴포저블 함수를 화면에 렌더링할 수 있는 UI 계층 구조로 변환하는 과정입니다. Jetpack Compose의 핵심 작동 방식이며, 프레임워크가 상태 변화를 추적하고 UI를 효율적으로 갱신하는 토대가 됩니다. Composition은 다음과 같은 방식으로 만들고 관리할 수 있습니다.

### ComponentActivity.setContent() 사용하기 {#using-setcontent}

Composition을 만드는 가장 흔한 방법은 `ComponentActivity` 또는 `ComposeView` 가 제공하는 `setContent` 함수를 사용하는 것입니다. 이 함수는 Composition을 초기화하고 그 안에 표시할 콘텐츠를 정의합니다.

```kotlin
import androidx.activity.ComponentActivity
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.setContent

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            MyComposableContent()
        }
    }
}

@Composable
fun MyComposableContent() {
    // UI 컴포넌트를 정의합니다.
}
```
{title="setContent.kt"}

위 코드처럼 `setContent` 는 컴포저블 함수를 렌더링하고 **Composition** 을 시작하는 책임을 맡으며, Compose UI의 **진입점(entry point)** 역할을 합니다.

`ComponentActivity.setContent` 의 내부를 들여다보면 결국 `ComposeView` 위에서 동작한다는 사실을 확인할 수 있습니다. `ComposeView.setContent` 를 호출해 **Composition** 을 초기화하고 만드는 구조입니다.

```kotlin
public fun ComponentActivity.setContent(
    parent: CompositionContext? = null,
    content: @Composable () -> Unit
) {
    val existingComposeView = window.decorView
        .findViewById<ViewGroup>(android.R.id.content)
        .getChildAt(0) as? ComposeView

    if (existingComposeView != null) with(existingComposeView) {
        setParentCompositionContext(parent)
        setContent(content)
    } else ComposeView(this).apply {
        // 인플레이션 과정과 attach 리스너가 처리되기 전에
        // setContent 를 호출하여 attach 시점에 ComposeView 가 Composition 을 만들도록 합니다.
        setParentCompositionContext(parent)
        setContent(content)
        // 콘텐츠 뷰를 설정하기 전에 view tree owner 들을 먼저 지정합니다.
        setOwners()
        setContentView(this, DefaultActivityContentLayoutParams)
    }
}
```
{title="ComponentActivity.setContent.kt"}

차근차근 짚어 보면, 이 함수는 먼저 액티비티의 뷰 계층에서 기존 `ComposeView` 를 찾고, 없을 때만 새로 만듭니다. 이미 `ComposeView` 가 있다면 새 `CompositionContext` 와 콘텐츠로 갱신하는 형태이고, 없다면 새 `ComposeView` 인스턴스를 만들어 액티비티 레이아웃에 붙입니다. 결국 Android를 타깃으로 하는 Compose UI는 내부적으로 전통적인 **View** 시스템 위에서 렌더링되며, 그 사이를 잇는 **다리(bridge)** 역할을 `ComposeView` 가 맡고 있습니다.

### XML 레이아웃에 Compose 끼워 넣기 {#composeview-in-xml}

Compose를 기존의 Android View 계층에 통합하려면 `ComposeView` 를 사용할 수 있습니다. XML로 정의된 레이아웃 안에 `ComposeView` 를 두고 거기에 컴포저블을 붙이면, `setContent` API가 내부에서 하는 일과 같은 방식으로 **Composition** 이 만들어집니다.

```kotlin
import androidx.compose.ui.platform.ComposeView

val composeView = ComposeView(context).apply {
    setContent {
        MyComposableContent()
    }
}
```
{title="ComposeView.kt"}

이 `ComposeView` 를 기존 `ViewGroup` 에 추가하거나, XML 레이아웃에 `<androidx.compose.ui.platform.ComposeView>` 태그로 포함시키면 됩니다.

### 요약 {#summary}

<tldr>

Composition은 컴포저블 함수를 실행해 Compose UI의 계층 구조를 만들고 관리하는 과정입니다. 새 Composition을 만들려면 컴포저블 함수로 UI를 정의한 뒤 `ComponentActivity.setContent` 또는 `ComposeView.setContent` 같은 메커니즘으로 초기화하면 됩니다. 두 방식 모두 결국 `ComposeView` 위에서 동작하며, 이 `ComposeView` 가 전통적인 View 시스템과 Compose UI를 연결하는 다리 역할을 합니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) ComposeView 는 전통적인 View 시스템과 Compose UI를 어떻게 연결하며, 언제 직접 사용하면 좋을까요?">

`ComposeView` 는 Android의 표준 View 계층에 들어가는 **컨테이너 View** 이면서 동시에 그 안에 Compose Composition 을 띄우는 매개체입니다. 내부적으로는 `View.onAttachedToWindow` 시점에 Compose 런타임을 부트스트랩해 Composition 을 만들고, 이후에는 일반 View 처럼 부모 ViewGroup 의 측정·배치·드로잉 흐름에 참여합니다. 즉 외부에서 보면 그냥 `View` 한 장이 있는 셈이지만, 그 안에서는 컴포저블로 정의한 UI가 별도의 Compose 파이프라인으로 그려지는 구조입니다.

이 다리 역할 덕분에 마이그레이션과 점진적 도입이 자연스러워집니다. 기존 Activity/Fragment 의 XML 레이아웃 가운데 일부 영역만 `<androidx.compose.ui.platform.ComposeView>` 로 바꾸고 그 안에서 `setContent { ... }` 로 컴포저블을 띄우면, 한 화면 안에서 View 와 Compose 를 공존시킬 수 있습니다. RecyclerView 의 ViewHolder 안에서 `ComposeView` 를 사용해 셀 자체만 Compose로 그리는 패턴도 가능합니다. 반대 방향, 즉 Compose 안에 기존 View 를 끼워 넣어야 할 때는 `AndroidView` 를 사용하는 것이 짝꿍이 됩니다.

언제 직접 `ComposeView` 를 사용하느냐 하면 보통 다음 두 상황입니다. 첫째, **앱이 이미 View 시스템 기반인데 일부 화면이나 위젯만 Compose 로 다시 작성** 하고 싶을 때입니다. 둘째, **다른 라이브러리/프레임워크가 View 단위 API만 제공** 해서, 그 위에 Compose UI를 얹어야 할 때입니다. 한 가지 주의할 점은 `ComposeView` 마다 자체 Composition 을 가진다는 사실입니다. 같은 화면에 여러 `ComposeView` 를 두면 그 만큼 Composition 컨텍스트가 늘어나므로, 많이 흩어 놓기보다는 의미 있는 단위로 묶는 것이 일반적으로 더 깔끔합니다.

</def>
</deflist>
