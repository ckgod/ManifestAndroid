# Q37) Canvas

## Canvas란 무엇이며 어떻게 활용하나요? {#C1}

`Canvas`는 커스텀 뷰를 위한 핵심 구성 요소입니다. 
이는 화면이나 `Bitmap`과 같은 다른 그리기 표면에 그래픽을 직접 렌더링하기 위한 인터페이스를 제공합니다. 
`Canvas`는 개발자에게 그리기 프로세스에 대한 완전한 제어권을 부여하여 커스텀 뷰, 애니메이션 및 시각적 효과를 만드는 데 일반적으로 사용됩니다.

### Canvas 작동 방식 {#C2}

`Canvas` 클래스는 도형, 텍스트, 이미지 및 기타 콘텐츠를 그릴 수 있는 2D 그리기 표면을 나타냅니다. 
이 클래스는 `Paint` 클래스와 밀접하게 상호 작용하며, `Paint` 클래스는 색상, 스타일, 선 두께를 포함하여 그려진 콘텐츠가 어떻게 보여야 하는지 정의합니다. 
커스텀 뷰의 `onDraw()` 메서드를 재정의할 때, `Canvas` 객체가 전달되어 무엇을 그릴지 정의할 수 있습니다.

다음은 기본 커스텀 뷰의 예시입니다.

```kotlin
class CustomView(context: Context) : View(context) {
    private val paint = Paint().apply {
        color = Color.BLUE
        style = Paint.Style.FILL
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        canvas.drawCircle(width / 2f, height / 2f, 100f, paint)
    }
}
```

이 예시에서 `onDraw()` 메서드는 `Canvas` 객체를 사용하여 커스텀 뷰 중앙에 파란색 원을 그립니다.

### Canvas의 일반적인 작업 {#C3}

`Canvas`는 다음과 같은 다양한 그리기 작업을 허용합니다.

* **도형**: `drawCircle()`, `drawRect()`, `drawLine()`과 같은 메서드를 사용하여 원, 사각형, 선과 같은 도형을 그릴 수 있습니다.
* **텍스트**: `drawText()` 메서드는 지정된 좌표와 모양으로 텍스트를 렌더링합니다.
* **이미지**: `drawBitmap()`을 사용하여 이미지를 렌더링합니다.
* **Custom 경로**: `Path` 객체를 `drawPath()`와 결합하여 복잡한 도형을 그릴 수 있습니다.

### 변환

`Canvas`는 스케일링, 회전 및 변환과 같은 변환을 지원합니다.
이러한 작업은 `Canvas`의 좌표계를 수정하여 복잡한 장면을 더 쉽게 그릴 수 있게 합니다.

* **변환 (Translation)**: `canvas.translate(dx, dy)`를 사용하여 `Canvas` 원점을 새 위치로 이동합니다.
* **크기 조절 (Scaling)**: `canvas.scale(sx, sy)`를 사용하여 특정 비율로 그림을 확대/축소합니다.
* **회전 (Rotation)**: `canvas.rotate(degrees)`를 사용하여 `Canvas`를 지정된 각도로 회전합니다.

이러한 변환은 누적되며 이후의 모든 그리기 작업에 영향을 미칩니다.

### 사용 사례

`Canvas`는 다음과 같이 고급 Custom 그래픽이 필요한 시나리오에서 특히 유용합니다.

1. **커스텀 뷰**: 표준 위젯으로는 구현할 수 없는 고유한 `UI` 구성 요소를 그립니다.
2. **게임**: 정밀한 제어로 게임 그래픽을 렌더링합니다.
3. **차트 및 다이어그램**: Custom 형식으로 데이터를 시각화합니다.
4. **이미지 처리**: 이미지를 프로그래밍 방식으로 수정하거나 결합합니다.

### 요약

`Canvas`는 화면에 Custom 그래픽을 렌더링하는 유연하고 유용한 방법을 제공합니다. 
도형, 텍스트, 이미지를 그리는 메서드와 변환을 활용하여 개발자는 풍부한 시각적이고 Custom된 경험을 만들 수 있습니다. 
이는 고급 그래픽 기능이 필요한 커스텀 뷰를 만드는 데 널리 사용됩니다.

> Q) `AndroidX` 라이브러리에서 지원하지 않는 복잡한 도형이나 `UI` 요소를 렌더링하기 위한 커스텀 뷰를 어떻게 만드나요? 어떤 `Canvas` 메서드와 `API`를 사용하시겠습니까?

#### A {collapsible="true"}
AndroidX와 같은 표준 라이브러리에서 지원하지 않는 복잡한 도형이나 UI요소를 구현하기 위해서는 `View` 클래스를 상속받아 Custom View를 직접 제작해야 합니다. 

이 과정의 핵심은 `Canvas`와 `Paint` 객체를 활용하여 `onDraw()` 메서드 내에서 픽셀 단위로 제어하는 것 입니다.

커스텀 뷰 제작 시 가장 빈번하게 Canvas와 Paint 객체를 다룹니다. 
1. Canvas: 무엇을 그릴지(모양, 도형)를 정의합니다. 
2. Paint: 어떻게 그릴지(색상, 스타일, 두께, 텍스트 크기)를 정의합니다.

##### 복잡한 도형을 위한 `Canvas` 메서드

1. **Path API**
   * 복잡한 커스텀 뷰의 90%는 Path 객체를 통해 이루어집니다. 직선과 곡선을 조합하여 임의의 다각형이나 비정형 도형을 만듭니다. 
   * **`Path.moveTo(x, y)`**: 펜의 시작점을 이동합니다. 
   * **`Path.lineTo(x, y)`**: 직선을 그립니다. 
   * **`Path.quadTo(x1, y1, x2, y2)`**: 베지어 곡선(Quadratic Bezier)를 그립니다. 부드러운 곡선이나 파동 효과를 낼 때 필수입니다.
   * **`Path.cubicTo(...)`**: 점 2개를 제어점으로 사용하는 더 복잡한 3차 베지어 곡선입니다.
   * **`Path.op()`**: 두 개의 Path를 합치거나, 교차 영역만 남기거나, 빼는 Boolean 연산을 수행합니다.
2. **그리기 메서드(`onDraw` 내부)**
   * **`canvas.drawPath(path, point)`**: 구성된 Path 객체를 실제로 화면에 그립니다.
   * **`canvas.drawArc(...)`**: 도넛 차트나 프로그레스 링을 그릴 때 사용합니다.
   * **`canvas.drawBitmap(...)`**: 비트맵 이미지를 특정 좌표에 그리거나 변형할 때 사용합니다.
3. **캔버스 조작 (Transformations)**
   * **`canvas.save()`** / **`canvas.restore()`**: 현재 캔버스의 상태(변형, 클리핑 등)를 저장하고 복구합니다. 필수적으로 짝을 맞춰 사용해야 합니다.
   * **`canvas.tranlate(dx, dy)`**: 원점(0,0)을 이동시킵니다.
   * **`canvas.rotate(degrees)`**: 캠버스를 회전시킵니다.
   * **`canvas.clipPath(path)`**: 특정 Path 영역 안쪽만 그려지도록 마스킹처리를 합니다. (예: 프로필 이미지를 별 모양으로 자르기)

##### 스타일링을 위한 `Paint` 및 고급 API

단순한 색 채우기를 넘어선 효과를 구현할 때 사용합니다. 

* **Anti-aliasing**: `paint.isAntiAlias = true` (계단 현상 제거, 필수 설정)
* **Shader**:
  * `LinearGradient`, RadialGradient, SweepGradient: 그라데이션 효과
  * BitmapShader: 이미지를 패턴으로 텍스처링하거나 도형 모양으로 이미지를 채울 때 사용
* **PorterDuffXfermode**: 두 레이어(Source와 Destination)를 겹칠 때의 블렌딩 모드를 정의합니다. (포토샵의 레이어 블렌딩과 유사, 투명한 구멍 뚫기 등에 사용)
* **ShadowLayer**: 뷰 내부에 커스텀 그림자 효과를 줍니다.


