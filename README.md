# Android Manifest Study Notes

이 문서는 [skydoves/manifest-android-interview](https://github.com/skydoves/manifest-android-interview) 내용을 기반으로 안드로이드 핵심 CS 지식을 학습하고 [IntelliJ Writerside](https://www.jetbrains.com/writerside/)로 정리한 프로젝트입니다.

## 주요 내용

-   Android Components (Activity, Service, Broadcast Receiver, Content Provider)
-   App Lifecycle (Process & Task, Activity Lifecycle)
-   UI Layer (View & Jetpack Compose)
-   Networking & Concurrency (Coroutines, OkHttp, Retrofit)
-   기타 안드로이드 핵심 CS 지식

> 이 프로젝트의 모든 학습 내용은 원본 저자인 [**skydoves**](https://github.com/skydoves)님께 저작권이 있습니다.

## 목차
* [1 Android](https://ckgod.github.io/ManifestAndroid/1-android.html)
  * [1 1 Android Framework](https://ckgod.github.io/ManifestAndroid/1-1-android-framework.html)
    * [Q1 Android](https://ckgod.github.io/ManifestAndroid/q1-android.html)
    * [Q2 Intent](https://ckgod.github.io/ManifestAndroid/q2-intent.html)
    * [Q3 Pending Intent](https://ckgod.github.io/ManifestAndroid/q3-pending-intent.html)
    * [Q4 Serializable Parcelable](https://ckgod.github.io/ManifestAndroid/q4-serializable-parcelable.html)
      * [Details Parcel And Parcelable](https://ckgod.github.io/ManifestAndroid/details-parcel-and-parcelable.html)
    * [Q5 Context](https://ckgod.github.io/ManifestAndroid/q5-context.html)
      * [Details 올바른 Context 사용법](https://ckgod.github.io/ManifestAndroid/details-올바른-context-사용법.html)
      * [Details Contextwrapper](https://ckgod.github.io/ManifestAndroid/details-contextwrapper.html)
      * [Details This Vs Basecontext](https://ckgod.github.io/ManifestAndroid/details-this-vs-basecontext.html)
    * [Q6 Application Class](https://ckgod.github.io/ManifestAndroid/q6-application-class.html)
    * [Q7 Androidmanifest](https://ckgod.github.io/ManifestAndroid/q7-androidmanifest.html)
    * [Q8 Activity Lifecycle](https://ckgod.github.io/ManifestAndroid/q8-activity-lifecycle.html)
      * [Details Lifecycle 인스턴스란](https://ckgod.github.io/ManifestAndroid/details-lifecycle-인스턴스란.html)
      * [Details 여러 Activity 간 수명 주기 변화](https://ckgod.github.io/ManifestAndroid/details-여러-activity-간-수명-주기-변화.html)
    * [Q9 Fragment 생명주기](https://ckgod.github.io/ManifestAndroid/q9-fragment-생명주기.html)
      * [Details Fragment의 Viewlifecycleowner 인스턴스](https://ckgod.github.io/ManifestAndroid/details-fragment의-viewlifecycleowner-인스턴스.html)
      * [Details Fragmentmanager와 Childfragmentmanager의 차이점](https://ckgod.github.io/ManifestAndroid/details-fragmentmanager와-childfragmentmanager의-차이점.html)
    * [Q10 Service](https://ckgod.github.io/ManifestAndroid/q10-service.html)
      * [Details Service의 생명주기](https://ckgod.github.io/ManifestAndroid/details-service의-생명주기.html)
      * [Details Forground Service](https://ckgod.github.io/ManifestAndroid/details-forground-service.html)
    * [Q11 Broadcastreceiver](https://ckgod.github.io/ManifestAndroid/q11-broadcastreceiver.html)
    * [Q12 Contentprovider](https://ckgod.github.io/ManifestAndroid/q12-contentprovider.html)
      * [Details 앱 시작 시 Contentprovider 사용하여 구성을 초기화하기](https://ckgod.github.io/ManifestAndroid/details-앱-시작-시-contentprovider-사용하여-구성을-초기화하기.html)
    * [Q13 Configuration Change](https://ckgod.github.io/ManifestAndroid/q13-configuration-change.html)
  * [1 2 Etc](https://ckgod.github.io/ManifestAndroid/1-2-etc.html)
    * [E1 Recyclerview 렌더링 과정](https://ckgod.github.io/ManifestAndroid/e1-recyclerview-렌더링-과정.html)
## 참고
- [skydoves/manifest-android-interview](https://github.com/skydoves/manifest-android-interview)
- [martup-reference](https://www.jetbrains.com/help/writerside/markup-reference.html) 