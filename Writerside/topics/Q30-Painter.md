# Q30) Painter

## Painter는 무엇인가요? {#what-is-painter}

`Painter` 는 이미지, 벡터 그래픽, 그 외의 drawable 콘텐츠를 렌더링하기 위해 Compose가 제공하는 추상화입니다. 이미지 로딩과 표시를 유연하게 다룰 수 있게 해 주며, 스케일링, 틴트, 커스텀 드로잉 로직 같은 기능을 함께 지원합니다.

### Painter의 동작 방식 {#how-painter-works}

전통적인 이미지 로딩 방식과 달리 `Painter` 는 이미지 자원을 그것을 표시하는 UI 컴포넌트로부터 분리시켜 줍니다. 이 분리 덕분에 다양한 이미지 소스와 함께 사용하기 좋습니다. 예를 들어 drawable 자원에는 `painterResource`, 벡터 이미지에는 `rememberVectorPainter`(반환 타입은 `VectorPainter`) 같은 식입니다.

Compose UI는 다음과 같은 기본 painter 구현을 제공합니다.

- `painterResource(id)` — `res/drawable` 폴더의 이미지를 불러옵니다.
- `ColorPainter(color)` — 영역을 단색으로 채웁니다.
- `rememberVectorPainter(image = ImageVector)` — `ImageVector` 로부터 동적으로 `VectorPainter` 를 만들어 줍니다.

### 사용 예시 {#example-usage}

다음은 `Painter` 를 `Image` 컴포저블과 함께 사용하는 예시입니다.

```kotlin
@Composable
fun DisplayImage() {
    val painter = painterResource(id = R.drawable.skydoves_image)
    Image(
        painter = painter,
        modifier = Modifier.size(100.dp),
        contentDescription = "Sample Image",
    )
}
```
{title="PainterExample.kt"}

`painterResource` 가 drawable 자원으로부터 이미지를 불러오고, `Image` 컴포저블이 그 `Painter` 를 받아 지정된 크기로 화면에 그립니다.

벡터 이미지의 경우 `rememberVectorPainter` 가 `VectorPainter` 를 만들어 주며, 다음과 같이 사용할 수 있습니다.

```kotlin
@Composable
fun DisplayVector() {
    val vectorPainter = rememberVectorPainter(image = Icons.Default.Star)
    Image(
        painter = vectorPainter,
        modifier = Modifier.size(50.dp),
        contentDescription = "Vector Icon",
    )
}
```
{title="VectorPainterExample.kt"}

`rememberVectorPainter` 는 `ImageVector` 로부터 `VectorPainter` 를 만들고, `Image` 가 그 painter 로 벡터를 손실 없이 스케일링하면서 그려 줍니다.

### 핵심 특징 {#key-features}

`Painter` 객체는 Jetpack Compose에서 그려질 수 있는 요소를 표현하는 도구로, Android의 전통적인 `Drawable` API의 자리를 대체합니다. 이미지나 그래픽이 어떻게 렌더링될지를 정의할 뿐 아니라, 그 painter 를 사용하는 컴포저블의 측정과 배치에도 영향을 줍니다.

커스텀 painter 가 필요하다면 `Painter` 클래스를 상속해 `onDraw` 메서드를 구현하면 됩니다. `onDraw` 안에서는 `DrawScope` 에 접근할 수 있어 그래픽을 직접 그릴 수 있고, 이를 통해 컴포저블 안에 어떤 콘텐츠를 어떻게 그릴지를 완전히 제어할 수 있습니다.

### 요약 {#summary}

<tldr>

`Painter` 는 이미지와 벡터 렌더링을 단순화하면서 스케일링·커스터마이즈의 유연성을 함께 제공하는 추상화입니다. `Painter` 와 `VectorPainter` 를 활용하면 이미지 자원을 효율적으로 불러오고, 비트맵·벡터 그래픽 모두를 Compose 친화적인 방식으로 다룰 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 직접 커스텀 Painter를 만들어 본 적이 있다면, 어떤 사용 사례였고 그리기 로직은 어떻게 구현했나요?">

가장 자주 만나는 사용 사례는 **단순한 도형 기반의 자리 표시자(placeholder)** 입니다. 예를 들어 이미지 로딩 라이브러리가 placeholder 슬롯에 그려 줄 painter 가 필요할 때, 그라데이션 + 코너 라운딩 + 약간의 노이즈가 들어간 단순한 painter 를 직접 만들어 두면 디자인 시스템 톤에 맞춰 일관된 placeholder 를 제공할 수 있습니다. 또 다른 사례는 **시머(shimmer) 효과** 처럼 시간에 따라 변하는 painter 입니다. `Animatable` 같은 상태와 결합해 `onDraw` 안에서 매 프레임 그라디언트의 위치를 옮기면, 이미지가 도착하기 전 자연스럽게 살아 움직이는 placeholder 를 만들 수 있습니다.

구현 시 가장 먼저 결정해야 하는 것은 **고유 크기(intrinsic size)** 입니다. `Painter` 는 `intrinsicSize` 프로퍼티를 통해 자기 자신의 자연스러운 크기를 표현할 수 있고, 이 값은 `Image(painter = ...)` 처럼 painter 가 직접 측정에 영향을 주는 자리에서 사용됩니다. 단순한 단색 채움처럼 자체 크기가 의미 없는 painter 라면 `Size.Unspecified` 를 반환하고, 도형 painter 라면 `Size(widthDp.toPx(), heightDp.toPx())` 식으로 자기 크기를 명시해 두면 호출 측 코드에서 별도 size 지정 없이도 자연스러운 크기로 그려집니다.

실제 그리기 로직은 `onDraw` 안의 `DrawScope` API로 작성합니다. `DrawScope` 는 `drawRect`, `drawCircle`, `drawRoundRect`, `drawPath`, `drawIntoCanvas` 같은 풍부한 도구를 제공하므로, 대부분의 시각 효과는 `onDraw` 안에서 합쳐 만들 수 있습니다. 두 가지 실수 포인트만 챙기면 됩니다. 첫째, `onDraw` 안에서는 무거운 객체 생성을 피하고 painter 의 필드에 미리 만들어 둔 `Paint`/`Path` 를 재사용하는 것이 좋습니다. 둘째, 외부 상태가 바뀔 때 painter 를 다시 그려야 한다면 painter 가 의존하는 값을 `mutableStateOf` 로 감싸 컴포지션이 그 변화를 감지할 수 있도록 만들어야 합니다.

</def>
</deflist>
