# Q28) Box

## Box는 무엇인가요? {#what-is-box}

`Box` 는 Jetpack Compose의 기본 레이아웃 컴포넌트로, 여러 자식 컴포저블을 하나의 부모 안에 **쌓아(stack)** 둘 수 있게 해 줍니다. 자식들을 자기 영역의 좌표 기준으로 배치하므로 오버레이, 정렬 제어, 레이어링 같은 처리에 잘 어울립니다. 배경 위 아이콘, 이미지 위 텍스트, 떠 있는 UI 요소 등 여러 시나리오에서 자연스럽게 쓰입니다.

### Box의 동작 방식 {#how-box-works}

`Box` 는 기본적으로 자식들을 좌상단 정렬로 배치하지만, `contentAlignment` 파라미터로 정렬 방식을 바꿀 수 있습니다. 추가로 `Modifier` 프로퍼티를 통해 크기, 패딩, 배경, 클릭 동작 같은 부분을 자유롭게 커스터마이즈할 수 있습니다.

`Column` 과 `Row` 가 자식을 순차적으로 정렬하는 것과 달리, `Box` 는 자식들을 스택처럼 겹쳐 배치하므로 UI 컴포넌트를 레이어로 쌓는 데 적합합니다.

### 사용 예시 {#example-usage}

다음 예시는 이미지 위에 텍스트를 오버레이하는 모습을 보여 줍니다.

```kotlin
@Composable
fun ImageWithOverlay() {
    Box(
        modifier = Modifier.size(200.dp),
        contentAlignment = Alignment.BottomCenter
    ) {
        Image(
            painter = painterResource(id = R.drawable.skydoves_image),
            contentDescription = "Background Image"
        )
        Text(
            text = "Hello, skydoves!",
            color = Color.White,
            modifier = Modifier
                .background(Color.Black.copy(alpha = 0.5f))
                .padding(8.dp)
        )
    }
}
```
{title="BoxExample.kt"}

이 예시에서:

- `Box` 가 `Image` 와 `Text` 를 자기 영역 안에 함께 배치합니다.
- `contentAlignment = Alignment.BottomCenter` 가 두 자식을 영역 하단 중앙으로 정렬합니다.
- 텍스트에는 가독성을 위해 반투명 배경이 적용되었습니다.

### 핵심 기능 {#key-features}

`Box` 는 두 가지 핵심 기능을 통해 UI 디자인의 다재다능한 도구가 됩니다. 첫째, 한 레이아웃 안에 여러 자식을 **stack** 해 둘 수 있어 UI 요소를 겹쳐 배치하기 좋습니다. 둘째, `contentAlignment` 로 부모 수준의 정렬을 지정하거나 `Modifier.align()` 으로 개별 자식의 정렬을 따로 설정할 수 있어 정렬 제어가 유연합니다.

### 요약 {#summary}

<tldr>

`Box` 는 같은 부모 안에서 UI 요소를 겹쳐 두기 위한 단순하면서도 유용한 레이아웃 컴포저블입니다. 콘텐츠 오버레이, 배경 효과, 요소 정렬 제어가 필요한 자리에서 특히 잘 어울립니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Column 이나 Row 대신 Box 를 선택하는 시나리오는 어떤 경우이며, Box 는 자식 컴포저블을 어떻게 다르게 처리하나요?">

선택 기준은 자식들 사이의 **공간 관계** 가 어떤 형태인가입니다. `Column` 과 `Row` 는 자식을 한 방향으로 차곡차곡 배열하므로, 자식들 사이에 "앞/뒤" 라는 시간적 순서가 필요한 화면에 어울립니다. 반면 `Box` 는 자식들을 같은 영역 안에 겹쳐 두므로, 자식들 사이의 관계가 "동시에 존재" 에 가까운 시나리오에 잘 맞습니다. 이미지 위 텍스트, 카드 위 그림자, 화면 위 토스트, 콘텐츠 위 로딩 인디케이터 같은 패턴이 모두 Box 의 영역입니다.

`Box` 는 자식들을 스택 순서대로 그려 줍니다. 즉 람다 안에서 먼저 호출된 자식이 아래쪽 레이어에, 나중에 호출된 자식이 위쪽 레이어에 그려집니다. 이 단순한 규칙 덕분에 z-index 같은 별도 개념 없이도 코드의 호출 순서가 곧 시각적 레이어 순서가 됩니다. 또한 자식의 크기는 `Box` 자체의 영역에 영향을 주지 않고, `Box` 는 콘텐츠 중 가장 큰 자식 크기에 맞춰 자기 자신의 크기를 결정합니다. 그래서 모든 자식을 채우고 싶다면 `Modifier.matchParentSize()` 또는 `fillMaxSize()` 를 자식에 명시해 주는 패턴이 자주 등장합니다.

마지막 차이는 정렬 방식입니다. `Column` 의 `verticalArrangement`, `Row` 의 `horizontalArrangement` 가 자식들 사이의 **간격 분배** 를 다룬다면, `Box` 의 `contentAlignment` 는 자식 각각이 부모 영역 안의 **어느 위치** 에 자리 잡을지를 결정합니다. 즉 Column/Row 가 "여러 항목을 어떻게 늘어놓을 것인가" 를 묻는다면, Box 는 "각 항목을 부모 영역 안 어디에 둘 것인가" 를 묻는 도구라고 보면 둘의 역할이 깔끔하게 분리됩니다.

</def>
<def title="Q) Box 의 contentAlignment 파라미터와 자식의 Modifier.align() 은 어떻게 다르며, 둘을 함께 사용할 수 있나요?">

두 API 의 출발점이 다릅니다. `contentAlignment` 는 `Box` 자체에 지정하는 **기본 정렬 정책** 으로, 별도의 정렬을 명시하지 않은 모든 자식에 적용됩니다. 반면 `Modifier.align(...)` 은 특정 자식에만 붙는 **개별 정렬 오버라이드** 로, 그 자식 한 명에 대해서만 부모의 기본 정책을 무시하고 새 정렬을 적용합니다. 결과적으로 `contentAlignment` 는 "이 박스 안의 기본 정렬은 이렇게 하자" 라는 선언이고, `Modifier.align` 은 "이 자식만 다르게 두고 싶다" 라는 예외 표현이 됩니다.

두 API는 **함께 사용할 수 있고, 그것이 일반적인 패턴** 입니다. 예를 들어 `Box(contentAlignment = Alignment.Center) { ... }` 으로 박스 전체를 가운데 정렬해 두고, 그 안의 닫기 버튼만 `Modifier.align(Alignment.TopEnd)` 로 우상단에 붙이는 식의 코드가 자주 등장합니다. 이 경우 닫기 버튼은 자기 자신에 한해 우상단으로 보내지고, 나머지 자식들은 박스의 기본 가운데 정렬을 그대로 따릅니다. 마치 디자인 시스템의 "기본 스타일 + 예외" 모델과 닮아 있어 의도가 명확하게 드러나는 구성입니다.

한 가지 유의할 점은 **`Modifier.align` 은 자식 자신의 modifier 체인 안에 있어야 의미를 갖는다** 는 것입니다. `Modifier.align` 은 `BoxScope` 안에서만 노출되는 확장이므로, 자식 컴포저블이 `Box` 의 직접 자식일 때만 사용 가능합니다. 또한 자식의 너비/높이가 박스 영역보다 클 경우에는 정렬이 시각적으로 의미를 잃을 수 있으므로, `Modifier.size`, `wrapContentSize` 같은 크기 관련 modifier 와의 순서를 함께 신경 써야 의도한 결과가 나옵니다.

</def>
</deflist>
