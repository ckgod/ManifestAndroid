# Details: BoxWithConstraints

## BoxWithConstraints란? {#what-is-boxwithconstraints}

`BoxWithConstraints` 는 컴포지션 시점에 부모의 레이아웃 제약(constraints)에 접근할 수 있게 해 주는 고급 레이아웃 API입니다. 일반 `Box` 와 달리, 사용 가능한 공간이나 크기 제약을 기준으로 UI 결정을 동적으로 내릴 수 있어 반응형 디자인이나 적응형 레이아웃에 잘 어울립니다.

### BoxWithConstraints의 동작 방식 {#how-it-works}

`BoxWithConstraints` 를 사용하면 컴포저블이 `Constraints` 스코프를 받아 `maxWidth`, `maxHeight`, `minWidth`, `minHeight` 같은 프로퍼티에 접근할 수 있습니다. 이 값들은 그 컴포저블이 차지할 수 있는 영역을 나타내며, 이를 기반으로 UI를 조정할 수 있습니다. 화면 크기, 윈도우 제약, 부모 레이아웃 크기 등에 따라 UI 요소가 동적으로 적응해야 하는 시나리오에 특히 유용합니다.

### 사용 예시 {#example-usage}

다음 예시는 사용 가능한 너비에 따라 텍스트 크기를 바꾸는 모습을 보여 줍니다.

```kotlin
@Composable
fun ResponsiveText() {
    BoxWithConstraints(
        modifier = Modifier.fillMaxWidth()
    ) {
        val textSize = if (maxWidth < 300.dp) 14.sp else 20.sp
        Text(
            text = "Hello, skydoves!",
            fontSize = textSize
        )
    }
}
```
{title="BoxWithConstraintsExample.kt"}

이 예시에서:

- `BoxWithConstraints` 가 사용 가능한 가로 공간을 의미하는 `maxWidth` 를 제공합니다.
- `maxWidth` 가 300.dp 보다 작으면 텍스트 크기를 14.sp 로, 그 이상이면 20.sp 로 설정합니다.
- 이 방식으로 텍스트가 화면 너비에 따라 동적으로 적응합니다.

### 핵심 특징 {#key-features}

`BoxWithConstraints` 는 컴포지션 스코프 안에서 레이아웃 제약에 접근할 수 있게 함으로써 반응형 디자인을 가능하게 합니다. 사용 가능한 공간에 따라 UI 요소를 동적으로 조정해야 할 때, 실시간 제약 값을 활용해 레이아웃을 조건부로 바꾸거나 타이포그래피를 적응시키거나 화면 크기에 따라 컴포넌트 배치를 재정렬할 수 있습니다.

다만 `BoxWithConstraints` 는 일반 `Box` 보다 추가 오버헤드가 있어 직접적인 대체재로 사용하면 안 됩니다. 내부적으로 `SubcomposeLayout` 으로 구현되어 있기 때문입니다.

```kotlin
@Composable
fun BoxWithConstraints(
    modifier: Modifier = Modifier,
    contentAlignment: Alignment = Alignment.TopStart,
    propagateMinConstraints: Boolean = false,
    content: @Composable BoxWithConstraintsScope.() -> Unit
) {
    val measurePolicy = maybeCachedBoxMeasurePolicy(contentAlignment, propagateMinConstraints)
    SubcomposeLayout(modifier) { constraints ->
        val scope = BoxWithConstraintsScopeImpl(this, constraints)
        val measurables = subcompose(Unit) { scope.content() }
        with(measurePolicy) { measure(measurables, constraints) }
    }
}
```
{title="BoxWithConstraintsInternals.kt"}

레이아웃 제약 접근이 정말로 필요한 경우에 한정해 사용하고, 그 외에는 일반 `Box` 를 사용해 불필요한 성능 비용을 피하는 것이 좋습니다.

### 요약 {#summary}

<tldr>

`BoxWithConstraints` 는 부모 제약을 기반으로 UI를 동적으로 조정할 수 있게 해 주는 레이아웃 컴포저블입니다. 다양한 화면 크기나 레이아웃 제약에 적응해야 하는 반응형 디자인에 특히 유용하며, 컴포저블이 디바이스 구성에 따라 유연하고 적응적으로 동작하도록 만들어 줍니다.

</tldr>
