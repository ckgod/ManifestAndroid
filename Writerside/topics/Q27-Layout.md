# Q27) Layout

## Layout 컴포저블은 무엇인가요? {#what-is-layout}

`Layout` 컴포저블은 자식 컴포저블의 측정과 배치를 직접 제어할 수 있게 해 주는 저수준 API입니다. `Column`, `Row`, `Box` 처럼 미리 정의된 동작을 가진 고수준 레이아웃 컴포넌트와 달리, `Layout` 은 특정 요구에 맞춰 직접 커스텀 레이아웃을 설계할 수 있도록 해 줍니다.

### Layout의 동작 방식 {#how-layout-works}

`Layout` 컴포저블은 자식들을 어떻게 측정하고 배치할지를 직접 정의하는 함수를 제공합니다. 이 과정은 두 단계로 나뉩니다.

1. **측정 단계(Measurement Phase)**: 부모가 전달한 제약(constraints) 안에서 각 자식의 크기를 결정합니다.
2. **배치 단계(Placement Phase)**: 사용 가능한 공간 안에서 각 자식의 위치를 결정합니다.

기본적인 `Layout` 컴포저블은 다음과 같은 구조를 가집니다.

```kotlin
@Composable
fun CustomLayout(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    Layout(
        content = content,
        modifier = modifier
    ) { measurables, constraints ->
        // 자식 측정
        val placeables = measurables.map { measurable ->
            measurable.measure(constraints)
        }

        // 레이아웃 자체의 크기 결정
        val width = constraints.maxWidth
        val height = placeables.sumOf { it.height }

        layout(width, height) {
            // 자식을 위에서 아래로 순차 배치
            var yPosition = 0
            placeables.forEach { placeable ->
                placeable.placeRelative(x = 0, y = yPosition)
                yPosition += placeable.height
            }
        }
    }
}
```
{title="CustomLayout.kt"}

### Layout의 핵심 구성 요소 {#key-components}

1. **자식 측정**: `measure()` 함수로 각 자식 컴포저블에 부모의 제약을 적용해 측정합니다.
2. **레이아웃 크기 결정**: `layout()` 함수가 레이아웃의 최종 너비/높이를 정의합니다.
3. **자식 배치**: `placeRelative()` 함수로 각 자식이 레이아웃 안의 어디에 위치할지를 정합니다.

### Layout을 언제 사용하나 {#when-to-use}

`Layout` 컴포저블은 `Column`, `Row`, `Box` 같은 표준 레이아웃 컴포넌트가 제공하는 것보다 더 정밀한 커스터마이즈가 필요할 때 사용합니다. 자식들이 어떻게 측정·배치되어야 할지에 대한 완전한 제어가 필요할 때 직접 측정과 배치 로직을 정의할 수 있습니다.

특히 staggered grid, 겹쳐 있는 요소, 콘텐츠에 따라 동적으로 크기가 결정되는 컴포넌트처럼 비정형 배치가 필요한 복잡한 UI에 적합합니다. `Layout` 은 제약과 측정에 직접 접근할 수 있게 해 주므로, 리컴포지션과 불필요한 재측정을 효율적으로 다루어 UI 성능을 끌어올리는 도구로도 활용됩니다.

또한 특정 동작과 스타일을 캡슐화하는 재사용 가능한 커스텀 레이아웃 컴포넌트를 만들 때도 유용합니다. UI 코드를 더 깔끔하고 유지보수하기 좋게 만들어 주며, 정밀한 정렬 규칙이나 적응형 레이아웃, 기존 컴포저블로는 표현하기 어려운 고유 배치를 다뤄야 할 때 자연스럽게 선택지가 됩니다.

### 요약 {#summary}

<tldr>

`Layout` 컴포저블은 측정과 배치에 대한 정밀한 제어를 제공해 커스텀 레이아웃을 설계할 수 있게 해 줍니다. 표준 레이아웃 컴포넌트로는 표현하기 어려운 고급 UI 시나리오에서, 자식들의 크기와 위치를 직접 정의하는 도구로 자리잡고 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 표준 Row나 Column 대신 Layout 컴포저블을 선택하는 시점은 언제인가요?">

판단 기준은 "표준 레이아웃이 제공하는 측정·배치 모델로 표현 가능한 UI인가" 입니다. `Row`, `Column`, `Box` 는 자식을 한 방향으로 배치하거나 단순히 겹쳐 두는 형태에 최적화되어 있어, 자식 크기에 종속적이고 단조로운 흐름을 만들기에는 충분합니다. 하지만 자식의 위치가 다른 자식의 크기에 의해 결정되거나, 부모 제약을 자식별로 다르게 흘려보내야 하거나, 일반적이지 않은 좌표 계산이 필요하다면 표준 컴포저블만으로는 부자연스러운 hack 코드가 늘어납니다. 이 자리에서 `Layout` 으로 측정과 배치를 직접 작성하는 편이 결과적으로 더 짧고 명료한 구현이 됩니다.

또 다른 신호는 **반복적으로 같은 구조가 만들어진다는 것** 입니다. 한 화면에서만 쓰는 일회성 배치라면 `Box` 안에 `Modifier.offset` 으로 위치를 잡는 정도로 충분할 수 있지만, 디자인 시스템에 들어가는 재사용 컴포넌트나 여러 화면에 등장하는 staggered grid 같은 패턴이라면 `Layout` 으로 캡슐화해 두는 편이 호출 측 코드를 깔끔하게 만들어 줍니다. 즉 "한 번만 만들고 끝"이 아니라 **이 배치 자체를 하나의 의미 단위로 부르고 싶을 때** `Layout` 의 가치가 두드러집니다.

마지막 기준은 성능입니다. 표준 컴포저블을 중첩해 흉내 낸 레이아웃은 측정 패스가 여러 번 일어나거나, 의도치 않은 리컴포지션 영역을 만들 수 있습니다. `Layout` 은 단일 측정 패스 안에서 명시적으로 자식의 측정과 배치를 다루므로, 동일한 결과를 더 적은 비용으로 만들어 낼 수 있는 경우가 많습니다. 이런 세 가지 — 표현 한계, 재사용성, 성능 — 가운데 두 가지 이상이 걸리면 그 시점이 `Layout` 을 꺼내야 할 때입니다.

</def>
<def title="Q) LazyVerticalGrid로는 표현하기 어려운 staggered grid 레이아웃을 만들어야 한다면 Layout으로 어떻게 구현하시겠습니까?">

가장 자연스러운 접근은 **고정 열 수의 staggered grid 형태로 모델링하고, 각 열의 누적 높이를 추적해 가장 짧은 열에 다음 항목을 채워 넣는 것** 입니다. `Layout` 의 측정 단계에서 모든 자식을 부모 제약(`constraints`)을 기반으로 한 번만 측정해 둔 뒤, 배치 단계에서 열 수만큼의 `IntArray(columnCount)` 같은 누적 높이 배열을 두고, 각 항목을 누적 높이가 가장 작은 열에 `placeRelative(x, y)` 로 배치하는 방식입니다. 이렇게 하면 항목 높이가 들쭉날쭉해도 좌·우 균형이 자연스럽게 잡힙니다.

핵심은 **자식별 너비 제약을 명시적으로 좁혀 주는 것** 입니다. 부모 제약을 그대로 자식에 전달하면 자식이 화면 전체 너비를 차지하려 할 수 있습니다. `measurable.measure(Constraints(maxWidth = columnWidth))` 처럼 한 열의 너비를 maxWidth 로 강제하면, 자식은 그 안에서 자신의 의도된 높이를 결정합니다. 컬럼 폭은 `(constraints.maxWidth - totalGap) / columnCount` 로 계산하고, 항목 사이 간격은 배치 단계에서 `y` 좌표에 더해 주면 됩니다. 마지막으로 레이아웃 전체 높이는 모든 열 누적 높이 중 가장 큰 값으로 결정해 `layout(width, maxColumnHeight) { ... }` 형태로 마무리합니다.

성능 측면에서 두 가지 안전장치를 챙기는 것이 좋습니다. 첫째, **항목이 매우 많은 화면이라면 LazyLayout 위에 staggered 로직을 얹어** 보이지 않는 항목까지 측정·배치하는 비용을 피해야 합니다. Compose 1.5+ 의 `LazyVerticalStaggeredGrid` 가 이 역할을 표준화해 주므로 우선 그 API로 충분한지 검토하는 것이 첫 단계입니다. 둘째, 항목들이 동일한 너비 제약을 받는 한 측정 결과를 한 번만 계산하면 되므로, 측정 단계에서 람다 안의 무거운 계산을 피하고 단순한 `placeable.height` 비교로만 배치를 결정하면 표준 패스 한 번에 깔끔하게 끝납니다.

</def>
</deflist>
