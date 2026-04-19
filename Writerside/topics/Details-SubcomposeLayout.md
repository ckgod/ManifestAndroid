# Details: SubcomposeLayout

## SubcomposeLayout이란? {#what-is-subcomposelayout}

`SubcomposeLayout` 은 한 레이아웃 패스 안에서 동적인 컴포지션을 가능하게 해 주는 저수준 API입니다. 어떤 UI 컴포넌트가 부모의 레이아웃 패스와 독립적으로 자식들을 다시 컴포즈해야 할 때 주로 사용됩니다. 자식 콘텐츠의 크기가 비동기 데이터에 의존하거나, 여러 번의 측정 패스가 필요한 경우에 특히 유용합니다.

### SubcomposeLayout의 동작 방식 {#how-it-works}

Jetpack Compose의 표준 레이아웃 시스템은 단일 측정 패스 모델을 따릅니다. 즉 각 컴포저블은 한 리컴포지션당 한 번만 측정됩니다. 그러나 어떤 UI 구조에서는 자식들을 여러 번 측정하거나, 레이아웃 제약이 결정될 때까지 컴포지션 자체를 미뤄야 합니다. `SubcomposeLayout` 은 이러한 유연성을 제공해, **측정 단계에서 자식들을 on-demand 로 컴포즈** 할 수 있게 해 줍니다.

`SubcomposeLayout` 이 어울리는 대표적인 시나리오는 다음과 같습니다.

- 컴포지션 단계에서 부모 제약에 접근해야 하지만, 일반 `Layout` 이나 `LayoutModifier` 로는 다루기 어려울 때(`BoxWithConstraints` 같은 경우).
- 한 자식의 측정 결과를 기반으로 다른 자식을 측정·배치해야 할 때 — subcomposition 의 가장 본질적인 동기.
- 사용 가능한 공간에 따라 lazily 항목을 컴포즈하고 싶을 때(예: 긴 리스트에서 보이는 항목만 렌더링하고 나머지는 스크롤 시점까지 미루기).
- 컴포저블의 크기가 컴포지션 시점에 동적으로 결정되는 콘텐츠에 의존할 때.
- 여러 단계의 독립적인 측정·배치를 거쳐야 하는 레이아웃 로직.
- lazy list 의 헤더처럼 입력이 변할 때만 리컴포즈되어야 하는 동적 UI.

### 사용 예시 {#example}

```kotlin
@Composable
fun DynamicContentLayout() {
    SubcomposeLayout { constraints ->
        val measurable = subcompose("content") {
            Text(text = "Hello, skydoves!")
        }.first().measure(constraints)

        layout(measurable.width, measurable.height) {
            measurable.placeRelative(0, 0)
        }
    }
}
```
{title="SubcomposeLayoutExample.kt"}

이 예시에서는 `subcompose("content")` 가 텍스트 콘텐츠를 동적으로 컴포즈합니다. `measure` 함수가 주어진 제약에 따라 자식의 크기를 계산하고, `layout` 함수가 측정된 자식을 그에 맞게 배치합니다.

### 사용 시 유의할 점 {#key-considerations}

`SubcomposeLayout` 은 강력한 유연성을 제공하지만, 잠재적인 성능 비용이 따라옵니다. 자식 요소들을 여러 번 측정하고 컴포즈할 수 있는 만큼, 잘못 사용하면 불필요한 리컴포지션이 늘어 성능을 떨어뜨릴 수 있습니다. 표준 레이아웃으로는 충분하지 않은 동적 UI 요소처럼, 정말로 다중 측정 패스가 필요한 경우에만 사용하는 것이 좋습니다. `SubcomposeLayout` 을 도입할 때는 리컴포지션이 정말 필요한 시점에만 일어나도록 설계해 효율을 유지해야 합니다.

### 요약 {#summary}

<tldr>

`SubcomposeLayout` 은 한 레이아웃 패스 안에서 동적인 subcomposition 을 가능하게 해 주는 유용한 API입니다. 콘텐츠 측정과 리컴포지션이 부모 레이아웃과 분리되어야 하는 시나리오에 가장 잘 어울리며, 강력한 유연성을 제공하지만 성능 함정을 피하기 위해 신중하게 사용해야 합니다.

</tldr>
