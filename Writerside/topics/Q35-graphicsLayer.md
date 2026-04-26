# Q35) graphicsLayer Modifier

## graphicsLayer Modifier를 어떻게 활용하나요? {#how-to-use-graphicslayer}

`graphicsLayer` 는 컴포저블에 변환, 클리핑, 컴포지팅 효과를 적용할 수 있게 해 주는 유용한 modifier 입니다. 컴포저블을 별도의 **draw layer** 로 렌더링함으로써 격리된 렌더링, 캐싱, 오프스크린 래스터라이즈 같은 최적화를 가능하게 만듭니다. `Canvas` 가 그리기 자체를 직접 다루는 도구라면, `graphicsLayer` 는 컴포저블의 모양을 더 선언적으로 바꾸면서도 컴포저블의 합성성(composability)을 유지하는 도구라고 볼 수 있습니다.

### graphicsLayer의 동작 방식 {#how-it-works}

`Modifier.graphicsLayer` 로 감싼 컴포저블은 **격리된 레이어** 를 만들고, 모든 그리기 연산을 나머지 UI와 분리해서 적용합니다. 그 결과 **스케일링, 이동, 회전, 알파 변경, 클리핑** 같은 변환을 이웃 컴포저블에 영향 없이 적용할 수 있습니다. 또한 `graphicsLayer` 는 하드웨어 가속을 활용하므로, 이러한 효과를 적용하면서도 과도한 리컴포지션 없이 효율적으로 동작합니다.

### 사용 예시 {#example-usage}

다음은 `graphicsLayer` 로 이미지를 스케일링하는 예시입니다.

```kotlin
@Composable
fun ScaledImage() {
    Image(
        painter = painterResource(id = R.drawable.skydoves_image),
        contentDescription = "Scaled Image",
        modifier = Modifier
            .graphicsLayer {
                scaleX = 1.5f
                scaleY = 1.2f
            }
            .size(200.dp)
    )
}
```
{title="GraphicsLayerScaleExample.kt"}

`scaleX = 1.5f` 는 가로로 1.5배, `scaleY = 1.2f` 는 세로로 1.2배 확대합니다.

### 변환(Transformations) 적용 {#applying-transformations}

`graphicsLayer` 는 이동, 회전, 원점 기준 스케일링 같은 다양한 변환을 지원합니다. 각각의 사용 모습을 살펴봅니다.

#### Translation (요소 이동)

```kotlin
@Composable
fun TranslatedImage() {
    Image(
        painter = painterResource(id = R.drawable.skydoves_image),
        contentDescription = "Translated Image",
        modifier = Modifier
            .graphicsLayer {
                translationX = 50.dp.toPx()
                translationY = -20.dp.toPx()
            }
            .size(200.dp)
    )
}
```
{title="GraphicsLayerTranslationExample.kt"}

`translationX` 는 이미지를 오른쪽으로 50.dp, `translationY` 는 위쪽으로 20.dp 이동시킵니다.

#### Rotation (X·Y·Z 축 회전)

```kotlin
@Composable
fun RotatedImage() {
    Image(
        painter = painterResource(id = R.drawable.skydoves_image),
        contentDescription = "Rotated Image",
        modifier = Modifier
            .graphicsLayer {
                rotationX = 45f
                rotationY = 30f
                rotationZ = 90f
            }
            .size(200.dp)
    )
}
```
{title="GraphicsLayerRotationExample.kt"}

- `rotationX` 는 가로 축 기준으로,
- `rotationY` 는 세로 축 기준으로,
- `rotationZ` 는 화면 평면 축 기준으로 회전을 적용합니다.

#### 클리핑과 모양(Shape)

`graphicsLayer` 는 `Shape` 와 `clip` 프로퍼티로 커스텀 클리핑을 지원합니다.

```kotlin
@Composable
fun ClippedBox() {
    Box(
        modifier = Modifier
            .size(200.dp)
            .graphicsLayer {
                clip = true
                shape = CircleShape
            }
            .background(Color.Blue)
    )
}
```
{title="GraphicsLayerClipExample.kt"}

`CircleShape` 가 콘텐츠를 원형으로 잘라 주고, `clip = true` 가 클리핑을 활성화합니다.

#### Alpha (투명도 제어)

`graphicsLayer` 는 `alpha` 로 투명도를 조정할 수 있습니다. `1.0f` 가 완전 불투명이고 `0.0f` 가 완전 투명입니다.

```kotlin
@Composable
fun TransparentImage() {
    Image(
        painter = painterResource(id = R.drawable.skydoves_image),
        contentDescription = "Transparent Image",
        modifier = Modifier
            .graphicsLayer {
                alpha = 0.5f
            }
            .size(200.dp)
    )
}
```
{title="GraphicsLayerAlphaExample.kt"}

`alpha = 0.5f` 는 이미지를 50% 투명도로 만들어 줍니다.

### Compositing 전략 {#compositing-strategies}

`graphicsLayer` 는 콘텐츠가 어떻게 렌더링될지를 결정하는 다양한 컴포지팅 전략을 제공합니다.

1. **Auto (기본값)**: 프로퍼티에 따라 자동으로 렌더링을 최적화합니다.
2. **Offscreen**: 콘텐츠를 오프스크린 텍스처에 먼저 렌더링한 뒤 합성합니다.
3. **ModulateAlpha**: 레이어 전체가 아니라 그리기 연산 단위로 알파를 적용합니다.

다음은 고급 블렌딩 효과를 위한 오프스크린 렌더링 예시입니다.

```kotlin
@Composable
fun OffscreenBlendEffect() {
    Image(
        painter = painterResource(id = R.drawable.skydoves_image),
        contentDescription = "Blended Image",
        modifier = Modifier
            .graphicsLayer {
                compositingStrategy = CompositingStrategy.Offscreen
            }
            .size(200.dp)
    )
}
```
{title="GraphicsLayerOffscreenExample.kt"}

이렇게 두면 `BlendMode` 같은 효과가 다른 컴포저블에 영향을 주지 않고 이 컴포저블에만 적용됩니다.

### 컴포저블을 Bitmap으로 캡처하기 {#composable-to-bitmap}

**Compose 1.7.0** 부터는 `graphicsLayer` 를 활용해 컴포저블을 비트맵으로 캡처할 수 있습니다. Android의 `Bitmap` 구조는 여전히 광범위하게 사용되고 있으므로, 컴포저블을 비트맵으로 추출해 두면 다양한 활용이 가능해집니다. 예를 들어 가우시안 블러처럼 산술 연산이 필요한 효과를 적용할 때 특히 유용합니다.

```kotlin
val coroutineScope = rememberCoroutineScope()
val graphicsLayer = rememberGraphicsLayer()

Box(
    modifier = Modifier
        .drawWithContent {
            graphicsLayer.record {
                drawContent()
            }
            drawLayer(graphicsLayer)
        }
        .clickable {
            coroutineScope.launch {
                val bitmap = graphicsLayer.toImageBitmap()
                // bitmap 을 저장하거나 공유합니다.
            }
        }
        .background(Color.White)
) {
    Text("Hello Compose", fontSize = 26.sp)
}
```
{title="GraphicsLayerToBitmapExample.kt"}

이 방식은 전체 UI를 다시 그리지 않고도 컴포저블을 비트맵으로 캡처할 수 있게 해 줍니다.

### 요약 {#summary}

<tldr>

`graphicsLayer` 는 컴포저블에 변환·클리핑·투명도·컴포지팅을 효율적으로 적용할 수 있게 해 주는 modifier 입니다. 스케일링, 회전, 이동, 고급 렌더링까지 폭넓게 다룰 수 있어 Compose 앱에서 정교한 시각 효과를 만들 때 핵심적인 도구가 됩니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 원형으로 클리핑된 이미지를 70% 투명도와 1.2배 스케일로 표시하려면 어떻게 구현하시겠습니까?">

세 가지 변환을 한 번에 받는 자리가 정확히 `graphicsLayer` 가 가장 빛나는 자리입니다. 한 컴포저블에 `Modifier.graphicsLayer { scaleX = 1.2f; scaleY = 1.2f; alpha = 0.7f; clip = true; shape = CircleShape }` 형태로 적어 두면, 격리된 draw layer 안에서 세 효과가 모두 적용된 결과만 외부에 합성됩니다. 클리핑과 알파를 같은 레이어 안에서 다루기 때문에 가장자리 처리도 자연스럽고, 추가 레이어 비용 없이 효과 세 개를 한 번에 처리할 수 있습니다.

비슷한 효과를 `Modifier.scale(1.2f).alpha(0.7f).clip(CircleShape)` 처럼 이어 붙이는 형태로도 표현할 수 있지만, 두 방식은 미묘하게 다른 동작을 합니다. 개별 modifier 들은 자기 단계에서 각각 변환을 적용하므로 일부 조합에서 가장자리 알파가 어긋나거나 추가 합성 패스가 일어날 수 있습니다. `graphicsLayer` 는 이 변환들을 하드웨어 가속이 적용된 단일 레이어 안에서 묶어 처리하므로, 효과가 많아질수록 표현 정확도와 성능 모두에서 더 안정적인 선택이 됩니다.

마지막 마감은 사용 맥락에 따라 결정됩니다. 이 효과가 자주 호출되거나 애니메이션과 결합된다면, 람다 안의 캡처를 줄이기 위해 `Modifier.graphicsLayer { ... }` 의 람다 인자를 활용해 변환 값을 매번 동일한 람다 인스턴스에서 읽도록 만드는 편이 좋습니다. 또한 클릭/드래그처럼 매 프레임 변환이 변하는 인터랙션에서는 `graphicsLayer` 가 변경 시 전체 UI가 아닌 해당 레이어만 다시 그리게 만들어, 이웃 컴포저블의 리컴포지션을 줄여 주는 추가 이점도 함께 따라옵니다.

</def>
<def title="Q) graphicsLayer 의 목적은 무엇이며, scale·rotate·alpha 같은 다른 modifier 대신 언제 사용해야 하나요? graphicsLayer 가 렌더링 성능과 컴포저블 격리에 어떤 영향을 주나요?">

`graphicsLayer` 의 본질은 **여러 시각 효과를 하나의 격리된 draw layer 위에서 한 번에 적용** 한다는 점에 있습니다. `scale`, `rotate`, `alpha`, `clip` 같은 modifier 들도 각각 독립적으로 사용하면 충분히 잘 동작하지만, 이 효과들을 두 개 이상 동시에 적용하거나 매 프레임 빠르게 바꿔야 한다면 `graphicsLayer` 한 줄로 묶는 편이 더 좋은 선택이 됩니다. 한 레이어 안에서 세 가지 변환을 동시에 적용하므로 추가 합성 패스가 줄고, 효과 사이의 시각적 정합성도 자연스럽게 맞춰집니다.

성능 측면에서의 장점은 **렌더링 격리** 와 **하드웨어 가속** 두 가지입니다. graphicsLayer 가 만드는 별도의 draw layer 는 GPU 텍스처에 캐시될 수 있어, 자식 콘텐츠 자체가 바뀌지 않는 한 같은 비트맵을 재사용해 합성할 수 있습니다. 이 덕분에 자주 변하는 변환(예: 드래그 중 translation, 펼침 애니메이션의 scale, 페이드 아웃의 alpha)을 매 프레임 적용해도 자식 컴포저블 자체는 다시 그리지 않게 되어, 큰 콘텐츠일수록 성능 차이가 두드러집니다. 또한 `BlendMode` 같은 효과는 격리된 레이어 위에서 적용되어야 의도대로 동작하는데, graphicsLayer 의 `compositingStrategy = Offscreen` 옵션이 그 자리를 정확히 채워 줍니다.

선택 기준을 단순화하면 다음과 같습니다. **하나의 효과만 가볍게 적용** 하는 경우라면 `Modifier.scale`, `Modifier.alpha`, `Modifier.clip` 같은 전용 modifier 가 더 짧고 직관적입니다. **여러 효과를 함께 적용하거나, 자주 바뀌는 인터랙션·애니메이션 자리에 효과를 두는 경우** 에는 `graphicsLayer` 가 표현 정확도와 성능 모두에서 우위를 가집니다. 마지막으로 **격리된 레이어가 본질적으로 필요한 경우**(예: BlendMode, 컴포저블을 비트맵으로 캡처) 에서는 graphicsLayer 가 사실상 유일한 선택지가 됩니다.

</def>
</deflist>
