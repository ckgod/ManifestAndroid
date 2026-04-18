# Q2) 선언형 UI 프레임워크로서의 Jetpack Compose

## 왜 Jetpack Compose는 선언형 UI 프레임워크인가요? {#why-compose-is-declarative}

Jetpack Compose가 **선언형(declarative) UI 프레임워크** 로 분류되는 이유는, 개발자가 어떤 상태에서 UI가 **어떻게 보여야 하는지(what)** 만 기술하고, 상태가 바뀔 때 UI를 **어떻게 갱신할지(how)** 는 프레임워크에 맡기기 때문입니다. 이는 개발자가 직접 View 객체를 조작하면서 UI 일관성을 유지해야 했던 전통적인 **명령형(imperative)** 접근과는 분명히 다른 방식입니다.

### Jetpack Compose의 선언형 UI 핵심 특성 {#key-characteristics}

**상태 주도 UI(State-Driven UI)**: 선언형 UI 프레임워크에서는 상태 관리가 프레임워크 자체에 내장되어 있습니다. 시스템이 각 컴포넌트의 상태를 추적하다가 상태가 바뀌면 자동으로 UI를 갱신해 줍니다. 개발자는 "이 상태에서는 UI가 어떻게 보여야 한다" 만 정의하면 되고, 실제 렌더링 갱신은 프레임워크가 처리합니다. Jetpack Compose에서는 모든 UI가 상태에 의해 구동되며, 상태가 변하면 리컴포지션이 트리거되어 영향을 받는 부분만 갱신됩니다.

**컴포넌트를 함수/클래스로 정의**: 선언형 UI는 UI 요소를 모듈화된 함수나 클래스로 정의하도록 권장합니다. 한 컴포넌트가 UI 레이아웃과 동작을 함께 기술하기 때문에, XML 같은 마크업 언어와 Kotlin/Java 같은 네이티브 언어 사이의 거리감이 자연스럽게 줄어듭니다. Compose에서는 `@Composable` 함수가 재사용 가능한 UI 컴포넌트의 단위가 됩니다.

**직접적인 데이터 바인딩**: 선언형 UI에서는 모델 데이터를 UI에 직접 바인딩하므로, 두 영역을 수동으로 동기화하는 어댑터 코드가 사라집니다. Compose는 함수 파라미터로 데이터를 그대로 받아 UI에 흘려보내기 때문에, 별도의 데이터 바인딩 레이어 없이도 깔끔한 코드를 유지할 수 있습니다.

**컴포넌트 멱등성(idempotence)**: 같은 입력이 들어오면 항상 같은 결과를 만들어 내는 성질을 멱등성이라 부릅니다. Compose의 `@Composable` 함수는 본질적으로 멱등하도록 설계되어 있어, 같은 파라미터로 호출하면 같은 UI가 만들어집니다. 이는 예측 가능하고 안정적인 렌더링을 보장합니다.

### Jetpack Compose vs XML {#compose-vs-xml}

선언형 UI의 장점을 체감하려면 클릭 횟수를 표시하는 단순한 버튼 예시를 비교해 보는 것이 가장 빠릅니다.

```kotlin
@Composable
fun Main() {
    var count by remember { mutableStateOf(0) }
    CounterButton(count) {
        count++
    }
}

@Composable
fun CounterButton(count: Int, onClick: () -> Unit) {
    Button(onClick = onClick) {
        Text("Clicked: $count")
    }
}
```
{title="JetpackCompose.kt"}

이 코드가 선언형 UI의 4가지 원칙을 어떻게 만족시키는지 정리하면 다음과 같습니다.

1. **함수로 UI 정의**: `@Composable` 어노테이션이 붙은 함수는 Compose 컴파일러가 해석·변환하여 선언형 UI 코드를 만듭니다. UI를 함수/클래스로 정의한다는 첫 번째 원칙을 충족합니다.
2. **상태 관리**: Compose 런타임이 제공하는 `remember`가 컴포저블의 상태와 수명 주기를 효율적으로 관리합니다. 컴포넌트 안에서 상태가 자동 관리된다는 두 번째 원칙에 해당합니다.
3. **직접 데이터 바인딩**: `CounterButton`이 받은 `count` 파라미터가 곧바로 UI에 바인딩됩니다. 데이터와 UI가 직접 연결된다는 세 번째 원칙을 만족합니다.
4. **컴포넌트 멱등성**: 같은 입력이 주어지면 `CounterButton`은 항상 같은 UI를 만듭니다. 멱등성을 통한 신뢰성 있는 컴포넌트라는 네 번째 원칙을 충족합니다.

이번에는 같은 UI를 XML 방식으로 구현해 보겠습니다.

```xml
<RelativeLayout
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:gravity="center"
    android:orientation="horizontal"
    android:padding="4dp">

    <Button
        android:id="@+id/button"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_centerInParent="true"
        android:text="Clicked: 0" />

</RelativeLayout>
```
{title="layout.xml"}

처음 보면 XML 자체도 "어떻게 보여야 하는지"를 기술하고 있어 선언형처럼 보입니다. 실제로 XML 레이아웃 정의 자체는 선언형의 성격을 가집니다. 차이가 드러나는 지점은 **상태와 로직 처리** 입니다. XML 기반 개발에서는 UI 구조와 속성은 XML로, 상태 관리와 UI 갱신은 별도의 명령형 코드로 작성됩니다.

```kotlin
var counter = 0

binding.button.setOnClickListener {
    counter++
    binding.button.text = counter.toString()
}
```
{title="Imperative.kt"}

UI 정의와 상태 갱신이 분리되어 있어, 두 영역을 수동으로 동기화하는 작업이 늘어납니다. 반면 Compose는 UI 정의와 상태 응답을 같은 Kotlin 코드 안에서 함께 표현할 수 있어, 코드의 응집도가 높아지고 별도의 명령형 핸들러가 필요하지 않습니다.

### 요약 {#summary}

<tldr>

Jetpack Compose는 "현재 상태에서 UI가 어떻게 보여야 하는지"만 선언하면 리컴포지션을 통해 자동으로 UI 갱신을 처리해 주는 선언형 UI 프레임워크입니다. 상태 주도 UI, 함수 기반 컴포넌트, 직접 데이터 바인딩, 멱등성이라는 네 가지 원칙을 따르므로, 동적인 UI를 만드는 일이 더 직관적이 되고 Android 앱 개발의 복잡도도 크게 줄어듭니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Jetpack Compose의 선언형 방식은 전통적인 명령형 XML UI 개발과 어떻게 다르며, 어떤 이점을 제공하나요?">

가장 큰 차이는 "UI 갱신의 책임이 어디에 있는가" 입니다. XML+View 시스템에서는 화면 구조는 XML로 선언하지만, 상태 변화에 따라 UI를 갱신하는 일은 개발자가 직접 코드로 작성해야 합니다. 버튼 텍스트가 카운트와 일치하도록 유지하려면 카운트가 바뀔 때마다 `binding.button.text = ...` 같은 명령을 빠짐없이 호출해야 하고, 이 동기화가 한 곳이라도 빠지면 화면과 데이터가 어긋납니다. 반면 Compose에서는 "이 상태에서 UI는 이렇게 보인다"만 선언해 두면, 상태가 바뀔 때 프레임워크가 알아서 영향을 받는 부분만 다시 그립니다.

이 차이가 코드 형태로 드러나는 모습을 보면 선언형의 이점이 더 분명해집니다. 명령형 방식은 Activity/Fragment 안에 클릭 리스너, 텍스트 갱신, View 참조 캐시, 상태 변수 같은 조각들이 흩어져 있어, 한 화면을 이해하려면 여러 곳을 함께 따라가야 합니다. Compose는 같은 화면을 만드는 코드가 한 함수 안에 응집되어 있어 읽기 쉽고, 같은 함수를 다른 화면이나 프리뷰에서 재사용하기에도 자연스럽습니다.

또한 선언형 모델은 테스트와 도구 친화성에도 도움이 됩니다. UI가 상태의 함수로 표현되기 때문에, 어떤 상태를 넘기면 어떤 UI가 나오는지를 단위 테스트나 프리뷰로 쉽게 검증할 수 있습니다. 결과적으로 코드가 더 응집되고, 상태와 UI 사이의 어긋남으로 인한 버그가 줄어들며, 새로 합류한 팀원이 화면을 이해하는 비용도 낮아집니다.

</def>
<def title="Q) Jetpack Compose는 컴포저블에서 어떻게 멱등성을 보장하며, 선언형 UI 시스템에서 멱등성이 왜 중요한가요?">

Compose에서 멱등성은 "같은 입력이 들어오면 같은 UI가 나온다"는 약속입니다. `@Composable` 함수는 외부 상태를 변형하지 않고 입력 파라미터만으로 결과를 만들어 내도록 설계됩니다. 함수 안에서 전역 변수를 바꾸거나 외부 컬렉션을 변경하는 식의 부수 효과(side effect)를 두지 않으면, 같은 파라미터로 다시 호출되었을 때 동일한 결과가 자연스럽게 보장됩니다. Compose 런타임 자체도 컴포저블이 멱등하다는 전제 위에서 동작하므로, 부수 효과는 `LaunchedEffect`, `SideEffect`, `DisposableEffect` 같은 전용 API 안으로 격리하는 것이 권장됩니다.

멱등성이 중요한 이유는 선언형 UI의 작동 모델 자체와 맞물려 있기 때문입니다. Compose는 상태 변화에 반응해 같은 컴포저블을 여러 번 호출(리컴포지션)하면서 UI를 다시 계산합니다. 만약 같은 입력에 대해 호출할 때마다 결과가 달라진다면, 어떤 호출의 결과를 신뢰해야 하는지가 모호해지고, 리컴포지션을 건너뛰는 최적화(skippable)나 캐싱이 모두 깨집니다. 또한 향후 Compose가 컴포저블을 병렬로 실행할 가능성을 열어 두고 있는데, 멱등성이 보장되지 않으면 이런 병렬화에서 정합성을 유지할 수 없습니다.

실용적인 관점에서도 멱등성은 디버깅과 테스트의 비용을 크게 줄여 줍니다. 멱등한 컴포저블은 프리뷰나 단위 테스트로 "어떤 상태일 때 어떤 화면이 나오는지"를 그대로 검증할 수 있고, 화면 회전이나 프로세스 재생성 후에도 일관된 결과를 만들어 냅니다. 결국 멱등성은 "선언형 UI가 약속하는 단순함"을 실제 코드 위에서 유지하기 위한 가장 기본적인 규약입니다.

</def>
</deflist>
