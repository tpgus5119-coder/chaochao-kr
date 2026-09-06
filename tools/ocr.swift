// 맥 내장 Vision OCR — 스캔본 PDF/이미지에서 한국어 글자를 읽어낸다. (설치 필요 없음, 오프라인)
// 쓰는 법:  ./ocr <이미지1.png> <이미지2.png> ...   → 파일마다 "=== 파일명" 다음에 본문
import Foundation
import Vision
import AppKit

let langs = ["ko-KR", "vi-VN", "en-US"]
for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        FileHandle.standardError.write("LOADFAIL \(path)\n".data(using: .utf8)!); continue
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.recognitionLanguages = langs
    req.usesLanguageCorrection = false          // 시험 문항은 원문 그대로여야 한다
    let h = VNImageRequestHandler(cgImage: cg, options: [:])
    print("=== \(path)")
    do {
        try h.perform([req])
        for o in (req.results ?? []) {
            if let c = o.topCandidates(1).first { print(c.string) }
        }
    } catch { FileHandle.standardError.write("OCRFAIL \(path) \(error)\n".data(using: .utf8)!) }
}
