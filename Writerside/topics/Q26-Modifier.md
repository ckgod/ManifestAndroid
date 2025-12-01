# Q26) Modifier

## Modifier란 무엇인가요? {#M1}
[Modifier](https://developer.android.com/develop/ui/compose/modifiers)는 `Jetpack Compose`에서 스타일과 동작을 적용하고 `Composable`을 체인 방식으로 수정할 수 있게 해주는 핵심 요소입니다.
이는 `UI` 요소에 `padding`, `size`, `alignment`, `click behavior`, `background` 및 상호작용과 같은 변형을 적용하는 유연한 방법을 제공합니다.

`Compose`는 선언적 `UI` 패러다임을 따르므로, `Modifier`는 `UI` 구성 요소의 핵심 로직을 수정하지 않고도 재사용 가능하고 유지보수 가능하게 만드는 데 중요한 역할을 합니다.

`Modifier`는 함수들을 함께 연결하여 적용되며, 여러 변형을 구성하는 구조화된 접근 방식을 가능하게 합니다.
체인의 각 함수는 이전에 적용된 수정 사항을 보존하면서 새로운 `Modifier` 인스턴스를 반환합니다.
이는 불변성을 보장하고 `Compose`가 `UI` 업데이트를 처리하는 방식을 최적화하여 성능을 향상시킵니다.

일반적으로 `Modifier`는 레이아웃 계층을 통해 원활하게 전파되어 루트 `Composable`에 정의된 속성을 `UI` 전체에 확장하고 유지할 수 있게 합니다.
이 접근 방식은 레이아웃 구성 및 스타일링의 일관성을 높이고 효율성을 향상시킵니다.
또한 `Modifier`는 상태 비저장(stateless)이며 표준 `Kotlin` 객체로 구현되므로 아래와 같이 함수 체인을 사용하여 쉽게 생성하고 구성할 수 있습니다.

```Kotlin
@Composable
fun Greeting(name: String) {
    Column(
        modifier = Modifier
            .padding(24.dp)
            .fillMaxWidth()
    ) {
        Text(text = "Hello,")
        Text(text = name)
    }
}
```

이 예시에서:
* `padding(24.dp)`은 `Column` 주위에 간격을 추가하여 화면 가장자리에 닿지 않도록 합니다.
* `fillMaxWidth()`는 `Column`이 사용 가능한 최대 너비로 확장되도록 하여 레이아웃의 일관성을 보장합니다.

> 기존 `XML` 시스템과 달리 `Jetpack Compose`에는 `margins` 개념이 없습니다.
> 대신 `Modifier` 체인 내에서 `padding`의 순서를 조정하여 유사한 동작을 구현할 수 있습니다.

## Modifier 순서의 중요성 {#M2}
`Modifier` 사용의 또 다른 중요한 측면은 적용되는 순서입니다.
`Modifier`는 순차적으로 체인화되므로 각 함수는 이전 함수를 래핑하고 그 위에 구축되어 구성 요소의 최종 모양과 동작에 직접적인 영향을 미치는 복합 구조를 형성합니다.
이 계층화 과정은 각 `Modifier`가 통제되고 예측 가능한 방식으로 작동하도록 보장합니다.
이는 수정 사항이 위에서 아래로 단계별로 적용되어 `UI`의 최종 레이아웃 및 상호작용 속성에 영향을 미치는 트리 탐색과 유사하게 작동합니다.

예를 들어, `padding` 앞에 `clickable`을 적용하면 `padding`을 포함한 전체 영역이 `clickable` 해지지만, `padding`을 먼저 적용하면 `clickable` 영역이 내부 콘텐츠로만 제한됩니다.

```Kotlin
@Composable
fun ArtistCard(onClick: () -> Unit) {
    Column(
        modifier = Modifier
            .clickable(onClick = onClick)
            .padding(21.dp)
            .fillMaxWidth()
    ) {
        // ...
    }
}
```

![modifier-order.png](modifier-order.png)

이 버전에서는 `padding` 영역도 `clickable`합니다. 

순서를 바꾸면:

```Kotlin
@Composable
fun ArtistCard(onClick: () -> Unit) {
    Column(
        modifier = Modifier
            .padding(21.dp)
            .clickable(onClick = onClick)
            .fillMaxWidth()
    ) {
        // ...
    }
}
```

이제 내부 콘텐츠만 `clickable`하고 `padding`은 클릭에 반응하지 않습니다. 
이는 `Modifier` 순서가 `Compose`의 동작에 어떻게 영향을 미치는지 보여줍니다.

![modifier-order-2.png](modifier-order-2.png)

다음은 `Modifier` 함수의 순서가 레이아웃에 어떤 영향을 미치는지 보여주는 또 다른 예시입니다.
이 구현은 `Modifier`의 순서를 신중하게 구성하여 간단한 온라인 인디케이터를 보여줍니다.

```Kotlin
@Composable
fun OnlineIndicator(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .size(60.dp) // 표시기의 전체 크기를 설정합니다.
            .background(VideoTheme.colors.appBackground, CircleShape) // 외부 배경을 적용합니다.
            .padding(4.dp) // 내부 콘텐츠 주위에 간격을 추가합니다.
            .background(VideoTheme.colors.infoAccent, CircleShape), // 내부 배경을 적용합니다.
    )
}
```

`Composable` 함수를 정의하고 `Android Studio`에서 Preview를 설정한 후, 결과를 시각화하여 `Modifier`의 스타일링 및 계층화가 의도한 대로 작동하는지 확인할 수 있습니다.

![outline-indicator.png](outline-indicator.png)

## 자주 사용되는 Modifier
`Jetpack Compose`는 `UI` 레이아웃, 모양 및 상호작용을 조정하기 위해 여러 내장 `Modifier`를 제공합니다.

### 크기 및 제약 조건
기본적으로 `Compose` 레이아웃은 자식(children)을 감싸지만, `size`, `fillMaxSize`, `fillMaxWidth`, `fillMaxHeight`를 사용하여 제약 조건을 지정할 수 있습니다.

```Kotlin
@Composable
fun ArtistCard() {
    Row(
        modifier = Modifier.size(width = 400.dp, height = 100.dp)
    ) {
        Text(text = "skydoves")
    }
}
```

일부 경우에 부모의 규칙에 따라 제약 조건이 무시될 수 있습니다.
부모의 제약 조건과 관계없이 고정된 `size`를 강제해야 하는 경우 `requiredSize()`를 사용하세요.

```Kotlin
@Composable
fun ArtistCard() {
    Row(
        modifier = Modifier.size(width = 400.dp, height = 100.dp)
    ) {
        Text(
            modifier = Modifier.requiredSize(150.dp),
            text = "skydoves"
        )
    }
}
```

여기서 부모 `height`가 `100.dp`로 설정되어 있더라도 `requiredSize()`로 인해 `Text`는 여전히 `150.dp`가 됩니다.

> `Compose`에서 레이아웃은 부모가 제약 조건을 설정하고 자식이 이를 따르도록 하는 제약 조건 기반 시스템을 따릅니다.
> 그러나 `requiredSize`와 같은 `Modifier`는 이러한 제약 조건을 재정의하거나 사용자 지정 레이아웃을 사용할 수 있습니다.
> 자식이 제약 조건을 무시하는 경우 시스템은 기본적으로 중앙에 배치하지만, 이 동작은 `wrapContentSize`로 조정할 수 있습니다.

### 레이아웃 위치 지정
요소를 원래 위치에서 상대적으로 이동하려면 `offset()`를 사용합니다.
`padding`과 달리 `offset`은 구성 요소의 `size`를 변경하지 않고 시각적으로 이동시킵니다.

```Kotlin
@Composable
fun ArtistCard() {
    Column {
        Text(text = "skydoves")
        Text(
            text = "Last seen online",
            modifier = Modifier.offset(x = 10.dp)
        )
    }
}
```

이는 두 번째 `Text component`를 오른쪽으로 `10.dp` 이동시킵니다.

### Scoped Modifier
일부 `Modifier`는 특정 `Composable` 스코프 내에서만 사용할 수 있습니다.
예를 들어, `matchParentSize()`는 `Box` 내에서만 사용할 수 있으며, 자식 구성 요소가 부모의 정확한 `size`를 차지하도록 보장합니다.

```Kotlin
@Composable
fun MatchParentSizeExample() {
    Box(modifier = Modifier.fillMaxWidth()) {
        Spacer(
            modifier = Modifier
                .matchParentSize()
                .background(Color.LightGray)
        )
        Text(text = "skydoves")
    }
}
```

여기서 `Spacer`는 부모 `Composable`인 `Box`와 일치하도록 `size`가 조정되며, `Text` 뒤의 `background color` 역할을 합니다.
`background color`를 `Text`의 `Modifier`에 직접 적용하는 것이 기술적으로 더 효율적이지만, 이 예시는 학습 목적을 위해 단순화된 것이므로 최상의 사례로 받아들이지 마십시오.

![scoped-modifiers.png](scoped-modifiers.png)

유사하게, `weight()` `Modifier`는 `Row` 및 `Column` 내에서만 사용할 수 있습니다. 
이는 자식이 형제(siblings)에 비해 유연한 공간을 차지하도록 허용합니다.

```Kotlin
@Composable
fun WeightedRow() {
    Row(modifier = Modifier.fillMaxWidth()) {
        Box(modifier = Modifier.weight(2f).background(Color.Red))
        Box(modifier = Modifier.weight(1f).background(Color.Blue))
    }
}
```

이 예시에서 첫 번째 빨간색 `Box`는 두 번째 `Box`의 두 배 공간을 차지합니다.

![compose-weight.png](compose-weight.png)

## 요약
`Modifier`는 `Jetpack Compose`의 필수 `API`로, 개발자가 `Composable`에 `size`, 레이아웃 및 상호작용 동작을 적용하여 사용자 지정할 수 있도록 합니다.
`Modifier`가 적용되는 순서는 동작에 영향을 미치며, 스코프가 지정된 `Modifier`는 해당 부모 `Composable`에 따라 신중하게 사용해야 합니다.
`Modifier`를 효율적으로 이해하고 적용하면 개발자는 유연하고 성능이 뛰어나며 재사용 가능한 `UI component`를 만들 수 있습니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) `Modifier`의 순서가 중요한 이유는 무엇인가요? 순서를 변경하면 다른 동작이 발생하는 예시를 제공해 주시겠어요?">

Modifier는 순차적으로 실행됩니다. 순서가 중요한 이유는 각 Modifier가 이전 Modifier를 감싸는 방식으로 순차적으로 적용되기 때문입니다.

가장 이해하기 쉬운 예시는 padding과 background 적용이 있습니다.

padding 먼저 적용하고 background를 적용하면 파란색 영역 안에 텍스트가 padding 만큼 떨어져서 위한 Composable이 됩니다.

background 적용 후 padding을 적용하면 파란색 영역안에 텍스트가 있고 파란색 영역 밖에 padding만큼 투명한 여백이 생깁니다.

</def>
</deflist>