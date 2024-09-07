"""
Title: LatexExtractorMixed
Author: Trojan
Date: 27-06-2024
"""
import logging
import os
from typing import Any, Optional
import cv2
import numpy as np

from PIL import Image

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class LatexExtractor:
    def __init__(self, downloaded_file_path: str, latex_model_english: Optional[Any] = None, latex_model_korean: Optional[Any] = None,
                 latex_model_japanese: Optional[Any] = None, latex_model_chinese_sim: Optional[Any] = None,
                 latex_model_chinese_tra: Optional[Any] = None):
        self.latex_model_english = latex_model_english
        self.latex_model_korean = latex_model_korean
        self.latex_model_japanese = latex_model_japanese
        self.latex_model_chinese_sim = latex_model_chinese_sim
        self.latex_model_chinese_tra = latex_model_chinese_tra
        self.model_dictionary = {
            "self.latex_model_english": [["en"], self.latex_model_english],
            "self.latex_model_korean": [['en', 'ko'], self.latex_model_korean],
            "self.latex_model_japanese": [['en', 'ja'], self.latex_model_japanese],
            "self.latex_model_chinese_sim": [['en', 'ch_sim'], self.latex_model_chinese_sim],
            "self.latex_model_chinese_tra": [['en', 'ch_tra'], self.latex_model_chinese_tra],
        }
        self.downloaded_file_path = downloaded_file_path

    def recognize_image(self, request_id: str):
        """Recognize text in the given image and optionally save the result."""
        try:
            image = Image.open(self.downloaded_file_path).convert('RGB')
            latex_results = {}
            count = 0
            for latex_model in self.model_dictionary:
                language = self.model_dictionary[latex_model][0]
                model = self.model_dictionary[latex_model][1]
                count += 1
                latex_data = model.recognize_text_formula(image, file_type='text_formula', return_text=False)
                latex_result = ""
                for data in latex_data:
                    latex_result += data.get("text", "")
                total_score = 0
                total_dicts = len(latex_data)
                for data in latex_data:
                    total_score += data["score"]
                final_confidence_score = total_score / total_dicts
                latex_results[f"model_{count}"] = {"text": latex_result, "confidence": final_confidence_score,
                                                   "language": language}

            highest_confidence_model = max(latex_results, key=lambda k: latex_results[k]['confidence'])
            highest_confidence = latex_results[highest_confidence_model]['confidence']
            highest_confidence_text = latex_results[highest_confidence_model]['text']
            # highest_confidence_language = latex_results[highest_confidence_model]['language']

            logging.info(f"Request id : {request_id} -> Extracted Text LatexOCRMixed: {highest_confidence_text}")
        except Exception as e:
            logging.error(f"Request id : {request_id} -> Error with exception: {e}")
            return f"error: {str(e)}"
        return highest_confidence_text, highest_confidence

    def recognize_image_single_language(self, model: Any, request_id: str, language: str):
        try:
            self.detect_and_remove_diagrams(request_id)
            image = Image.open(self.downloaded_file_path).convert('RGB')
            latex_results = {}
            latex_data = model.recognize_text_formula(image, file_type='text_formula', return_text=False)
            latex_result = ""
            for data in latex_data:
                latex_result += data.get("text", "")
            total_score = 0
            total_dicts = len(latex_data)
            for data in latex_data:
                total_score += data["score"]
            if total_dicts != 0:
                final_confidence_score = (total_score / total_dicts) * 100
            if total_dicts == 0:
                final_confidence_score = total_score * 100

            latex_results[f"model_{language}"] = {"text": latex_result, "confidence": final_confidence_score,
                                                   "language": language}

            logging.info(f"Request id : {request_id} -> Extracted Text LatexOCRMixed: {latex_result}")

        except Exception as e:
            logging.error(f"Request id : {request_id} -> Error with exception: {e}")
            return f"error: {str(e)}"
        return latex_result, final_confidence_score

    def detect_and_remove_diagrams(self, request_id: str):
        try:
            image = cv2.imread(self.downloaded_file_path)

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            mask = np.zeros(image.shape[:2], dtype=np.uint8)

            # Refine contours to filter out text or other small objects
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h
                    if aspect_ratio > 0.30:  # 0.60 worked somewhat well
                        cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)  # White contours
                        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        if w > 0.30 * image.shape[1] and h > 0.30 * image.shape[0]:
                            if w < 0.75 * image.shape[1] and h < 0.75 * image.shape[0]:
                                cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 255), -1)

            cv2.imwrite(self.downloaded_file_path, image)
            logging.info(f"Request id : {request_id} -> Diagrams found and removed from image.")
        except Exception as e:
            logging.error(f"Request id : {request_id} -> Error: {e}")
