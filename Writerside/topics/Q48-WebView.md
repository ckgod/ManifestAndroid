# Q48) WebView

## Android에서 웹 페이지를 어떻게 렌더링하나요? {#how-to-render-web-page}

`WebView`는 앱 내에서 웹 콘텐츠를 직접 표시하고 상호작용할 수 있는 다목적 Android 컴포넌트입니다. 앱에 내장된 미니 브라우저처럼 작동하여 웹 페이지 렌더링, HTML 콘텐츠 로딩, JavaScript 실행이 가능합니다. 최신 WebView 기능을 안전하게 활용하려면 [AndroidX Webkit](https://developer.android.com/reference/androidx/webkit/package-summary) 라이브러리를 사용하는 것이 좋습니다. 이 라이브러리는 하위 호환 API를 제공하여 기기의 Android 버전에 관계없이 최신 기능을 사용할 수 있습니다.

### WebView 초기화 {#initializing-webview}

WebView를 사용하려면 레이아웃 파일에 추가하거나 코드로 생성합니다.

```xml
<WebView
    android:id="@+id/webView"
    android:layout_width="match_parent"
    android:layout_height="match_parent" />
```
{title="activity_main.xml"}

```kotlin
val webView = WebView(this)
setContentView(webView)
```
{title="WebViewInit.kt"}

### 웹 페이지 로드 {#loading-web-page}

`loadUrl()` 메서드로 웹 페이지를 로드합니다. 인터넷 접근이 필요한 경우 `AndroidManifest.xml`에 권한을 추가해야 합니다.

```kotlin
val webView: WebView = findViewById(R.id.webView)
webView.loadUrl("https://www.example.com")
```
{title="WebViewLoad.kt"}

```xml
<uses-permission android:name="android.permission.INTERNET" />
```
{title="AndroidManifest.xml"}

### JavaScript 활성화 {#enabling-javascript}

웹 콘텐츠에 JavaScript가 필요한 경우 `WebSettings`에서 활성화합니다.

```kotlin
val webSettings = webView.settings
webSettings.javaScriptEnabled = true
```
{title="WebViewJavaScript.kt"}

### WebView 동작 커스터마이징 {#customizing-webview-behavior}

**페이지 탐색 가로채기**

`WebViewClient`를 설정하면 링크 클릭 시 외부 브라우저가 아닌 WebView 내에서 페이지를 탐색하도록 제어할 수 있습니다.

```kotlin
webView.webViewClient = object : WebViewClient() {
    override fun shouldOverrideUrlLoading(view: WebView, url: String): Boolean {
        view.loadUrl(url)
        return true
    }
}
```
{title="WebViewNavigation.kt"}

**파일 다운로드 처리**

`DownloadListener`를 사용하면 WebView에서 시작된 파일 다운로드를 앱에서 직접 관리할 수 있습니다.

```kotlin
webView.setDownloadListener { url, userAgent, contentDisposition, mimeType, contentLength ->
    // 파일 다운로드 처리 로직
}
```
{title="DownloadListener.kt"}

**JavaScript 코드 실행**

`evaluateJavascript()`를 사용해 WebView 내에서 JavaScript 코드를 직접 실행할 수 있습니다.

```kotlin
webView.evaluateJavascript("document.body.style.backgroundColor = 'red';") { result ->
    Log.d("WebView", "JavaScript 실행 결과: $result")
}
```
{title="EvaluateJavaScript.kt"}

### JavaScript와 Android 코드 연동 {#binding-javascript-to-android}

`addJavascriptInterface()` 메서드를 사용하면 JavaScript에서 Android 네이티브 기능을 호출할 수 있습니다. 예를 들어 JavaScript의 `alert()` 대신 Android 네이티브 Toast나 Dialog를 표시하는 것이 가능합니다.

```kotlin
class WebAppInterface(private val context: Context) {

    @JavascriptInterface
    fun showToast(message: String) {
        Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
    }
}

// WebView에 인터페이스 바인딩
val webView: WebView = findViewById(R.id.webview)
webView.settings.javaScriptEnabled = true
webView.addJavascriptInterface(WebAppInterface(this), "Android")
```
{title="WebAppInterface.kt"}

HTML 측에서는 다음과 같이 Android 인터페이스를 호출합니다.

```html
<button onclick="callAndroidFunction()">Click Me</button>
<script type="text/javascript">
function callAndroidFunction() {
    Android.showToast("Hello from JavaScript!");
}
</script>
```
{title="webview_example.html"}

### 보안 고려 사항 {#security-considerations}

`addJavascriptInterface()`는 유용하지만 중요한 보안 위험이 따릅니다. WebView에서 신뢰할 수 없는 HTML 콘텐츠를 로드하는 경우, 공격자가 악의적인 JavaScript를 주입하여 노출된 인터페이스를 악용할 수 있습니다.

- 꼭 필요한 경우에만 JavaScript를 활성화합니다.
- `setAllowFileAccess()`와 `setAllowFileAccessFromFileURLs()`는 무단 파일 접근을 방지하기 위해 신중하게 사용합니다.
- XSS나 URL 스푸핑 공격을 방지하기 위해 사용자 입력을 항상 검증하고 URL을 정제합니다.
- `@JavascriptInterface`로 노출하는 메서드가 보안 취약점을 유발하지 않도록 주의합니다.

### 요약 {#summary}

<tldr>
WebView는 Android 앱 내에서 웹 콘텐츠를 렌더링하는 핵심 컴포넌트입니다. `WebViewClient`로 탐색을 제어하고, 필요 시 JavaScript를 활성화하며, `addJavascriptInterface()`로 JavaScript와 Android 네이티브 코드를 연동할 수 있습니다. 다만 JavaScript 활성화와 인터페이스 노출은 XSS 등 보안 위험을 동반하므로 신중하게 다뤄야 합니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 외부 링크 클릭 시 사용자가 앱을 벗어나지 않도록 WebView 탐색을 효과적으로 처리하려면 어떻게 해야 하나요?">

`WebViewClient`를 구현하고 `shouldOverrideUrlLoading()`을 오버라이드하면 모든 URL 탐색을 앱 내 WebView에서 처리할 수 있습니다.

```kotlin
webView.webViewClient = object : WebViewClient() {
    override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
        val url = request.url.toString()
        // 외부 링크는 앱 내에서 로드
        view.loadUrl(url)
        return true
    }
}
```

추가로 뒤로 가기 버튼 처리도 구현하면 WebView 히스토리를 따라 이전 페이지로 돌아갈 수 있습니다.

```kotlin
override fun onBackPressed() {
    if (webView.canGoBack()) {
        webView.goBack()
    } else {
        super.onBackPressed()
    }
}
```

특정 도메인의 링크만 앱 내에서 열고, 외부 도메인은 브라우저로 위임하는 방식도 흔히 사용됩니다.

</def>
</deflist>
