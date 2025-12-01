# Q29) Arrangement, Alignment

## Arrangement와 Alignment의 차이점은 무엇인가요? {#AA1}
Jetpack Compose에서 Arrangement와 Alignment는 모두 레이아웃 내에 UI 요소를 배치하는 데 사용되지만, 각각 다른 목적을 가지고 있습니다. 이들의 차이점을 이해하면 UI 구성 요소를 효과적으로 구성하는 데 도움이 됩니다.

### Arrangement란 무엇인가요?
Arrangement는 Row 또는 Column과 같이 단일 방향으로 아이템을 정렬하는 레이아웃 내에서 여러 자식 composable의 간격과 분포를 제어합니다. 이는 레이아웃의 주 축을 따라 자식들이 어떻게 배치되는지를 결정합니다.

예를 들어, Row에서는 Arrangement가 아이템들이 수평으로 어떻게 간격을 두는지 정의하고, Column에서는 수직으로 어떻게 간격을 두는지 정의합니다.

```kotlin
@Composable
fun RowWithArrangement() {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(text = "Hello")
        Text(text = "skydoves")
    }
}
```

이 예시에서:
* `Arrangement.SpaceBetween`은 두 개의 `Text` composable이 사용 가능한 너비에 걸쳐 고르게 간격을 두도록 보장합니다.
* 첫 번째 `Text`는 시작점에 배치되고, 두 번째 `Text`는 끝점에 배치되며, 그 사이에 공간이 분배됩니다.

### Alignment란 무엇인가요? {#AA3}
Alignment는 부모 내에서 자식 composable이 교차 축을 따라 어떻게 배치되는지를 결정합니다. 이는 Box, Row, Column과 같은 레이아웃에서 요소들이 컨테이너의 경계에 상대적으로 어떻게 정렬되는지를 제어하는 데 사용됩니다.

* Row에서는 `Alignment`가 수직 배치에 영향을 미칩니다.
* Column에서는 `Alignment`가 수평 배치에 영향을 미칩니다.
* Box에서는 `Alignment`가 수평 및 수직 배치 모두에 영향을 미칩니다.

### Alignment 예시

```kotlin
@Composable
fun ColumnWithAlignment() {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(text = "Hello")
        Text(text = "skydoves")
    }
}
```

이 예시에서:
* `horizontalAlignment = Alignment.CenterHorizontally`는 두 `Text` 요소가 `Column` 내에서 중앙에 배치되도록 보장합니다.
* `Column`은 여전히 자식들을 수직으로 쌓지만, 이제 수평 축을 따라 중앙에 정렬됩니다.

### 주요 차이점
Arrangement는 여러 자식 요소를 주 축(Row의 경우 수평, Column의 경우 수직)을 따라 배치하는 데 사용됩니다. 이와 대조적으로 Alignment는 개별 요소를 부모 내에서 교차 축을 따라 배치하는 데 사용됩니다.

Jetpack Compose에서 효율적이고 잘 구성된 레이아웃을 구축하려면 이들을 올바르게 사용하는 것이 중요합니다. Arrangement와 Alignment는 서로 다른 목적을 가지고 있기 때문에 어떤 것을 사용해야 할지 결정할 때 종종 혼란을 야기할 수 있습니다. 이들의 분명한 역할을 이해하면 더 나은 레이아웃 결정을 내리고 불필요한 복잡성을 피하는 데 도움이 됩니다.

> {style="note"}
> **Arrangement와 Alignment의 차이점을 기억하는 창의적인 방법**
> 
> “Arrangement”는 “Array”와 비슷하게 들립니다 → 주 축을 떠올려 보세요. 배열이 여러 항목을 순서대로 담는 것처럼, Arrangement는 composable 그룹이 주 축(Row의 경우 수평, Column의 경우 수직)을 따라 어떻게 배치되는지를 제어합니다.
> 
> “Alignment”는 “Line”과 비슷하게 들립니다 → 교차 축에 있는 단일 항목(다른 축에서 단일 항목을 위한 선을 교차한다고 상상해 보세요). “Alignment”를 컨테이너 내에서 단일 항목을 상단, 중앙, 하단, 시작, 끝과 같은 가상의 선을 따라 배치하는 것으로 상상해 보세요.

### 요약
Arrangement와 Alignment는 모두 UI 요소를 배치하는 데 도움이 되지만, 서로 다른 축에서 작동하며 뚜렷한 목적을 가지고 있습니다. Arrangement는 여러 항목이 주 축을 따라 어떻게 간격을 두는지를 제어하고, Alignment는 부모 컨테이너 내에서 항목이 교차 축을 따라 어떻게 배치되는지를 결정합니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Arrangement와 Alignment의 차이점은 무엇인가요?">

</def>
</deflist>