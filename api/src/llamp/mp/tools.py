import json
import os
import re
from pathlib import Path
from typing import Optional

from emmet.core.summary import HasProps
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.pydantic_v1 import Field
from langchain.tools import BaseTool, Tool

from llamp.mp.schemas import (
    BondsSchema,
    DielectricSchema,
    ElasticitySchema,
    MagnetismSchema,
    OxidationSchema,
    PiezoSchema,
    RobocrysSchema,
    SimilaritySchema,
    StructureSchema,
    SummarySchema,
    SynthesisSchema,
    TasksSchema,
    ThermoSchema,
)
from llamp.utilities import MPAPIWrapper

# NOTE: https://python.langchain.com/docs/modules/agents/tools/custom_tools


class MPTool(BaseTool):
    name: str
    api_wrapper: MPAPIWrapper = Field(default_factory=MPAPIWrapper)

    def _count_token(self, response) -> int:
        '''TODO'''
        pass

    def _too_large(self, response) -> bool:
        '''TODO'''
        return self._count_token(response) > 200

    def _summarize(self, response) -> str:
        '''summarize w/ anthropic'''
        pass

    def _run(self, **query_params):
        _res = self.api_wrapper.run(
            function_name=self.name, function_args=json.dumps(query_params), debug=False
        )
        '''
        while self._too_large(_res):
            _res = self._summarize(_res)
        return _res
        '''
        return _res

    async def _arun(self, function_name: str, function_args: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("async is not supported yet")


class MaterialsSummary(MPTool):
    name: str = "search_materials_summary__get"
    description: str = (
        re.sub(
            r"\s+",
            " ",
            """useful when you need calulated or derived materials properties, also useful 
        when you need to perform filtering on chemical systems or sorting on materials 
        properties, also useful when you need high-level information about materials 
        (such as material_id) and use the results to perform further queries using 
        other tools. There is `MaterialsStructure` tool that is more suitable for 
        pymatgen structures retrieval and visualization""",
        )
        .strip()
        .replace("\n", " ")[0]
    )
    args_schema: type[SummarySchema] = SummarySchema

class MaterialsStructure(MPTool):
    name: str = "search_materials_structure__get"
    description: str = (
        re.sub(
            r"\s+",
            " ",
            """useful when you need to get the pymatgen structures on Materials 
            Project, can be used with filters like chemical system, formula, etc."""
        )
        .strip()
        .replace("\n", " ")[0]
    )
    args_schema: type[StructureSchema] = StructureSchema

    def _run(self, **query_params):
        _response =  super()._run(**query_params)

        print(_response)

        for entry in _response:
            material_id = entry['material_id']
            structure = entry['structure']

            out_dir = Path(__file__).parent.absolute() / '.tmp'
            os.makedirs(out_dir, exist_ok=True)
            fpath = out_dir / f'{material_id}.json'

            with open(fpath, 'w') as f:
                f.write(json.dumps(structure))

        return '[structures]' + ','.join(list(map(lambda x: x['material_id'], _response)))

class MaterialsElasticity(MPTool):
    name: str = "search_materials_elasticity__get"
    description: str = (
        re.sub(
            r"\s+",
            " ",
            """useful when you need elasticity properties like bulk modulus, shear modulus, 
        elastic anisotropy, Poisson ratio, elastic/compliance tensors, also useful when 
        you need to perform filtering and sorting elastic properties and retrieve the 
        qualified materials""",
        )
        .strip()
        .replace("\n", " ")[0]
    )
    args_schema: type[ElasticitySchema] = ElasticitySchema


class MaterialsSynthesis(MPTool):
    name: str = "search_materials_synthesis__get"
    description: str = (
        re.sub(
            r"\s+",
            " ",
            """useful when you need materials synthesis recipes and list out the reactions, 
        precursors, targets, operations, conditions, required devices and references""",
        )
        .strip()
        .replace("\n", " ")[0]
    )
    args_schema: type[SynthesisSchema] = SynthesisSchema


class MaterialsThermo(MPTool):
    name: str = "search_materials_thermo__get"
    description: str = (
        re.sub(
            r"\s+",
            " ",
            """useful when you need thermodynamic properties like mass density, atomic 
        density, formation energy, decomposition enthalpy, energy above hull, 
        equilibrium reaction energy, and raw DFT calculated energy, also useful when
        you want to compare the thermodynamic properties of materials with 
        material_ids""",
        )
        .strip()
        .replace("\n", " ")[0]
    )
    args_schema: type[ThermoSchema] = ThermoSchema


class MaterialsMagnetism(MPTool):
    name: str = "search_materials_magnetism__get"
    description: str = (
        re.sub(
            r"\s+",
            " ",
            """useful when you need magnetic properties like magnetic moment (magmoms), 
        magnetic ordering and symmetry, magnetic sites, magnetic type, also useful when 
        you need to perform filtering and sorting magnetic properties and retrieve the 
        qualified materials.""",
        )
        .strip()
        .replace("\n", " ")[0]
    )
    args_schema: type[MagnetismSchema] = MagnetismSchema


class MaterialsDielectric(MPTool):
    name: str = "search_materials_dielectric__get"
    description: str = (
        re.sub(
            r"\s+",
            " ",
            """useful when you need dielectric properties like dielectric constant, 
        dielectric tensor, refractive index (n), also useful when you 
        need to perform filtering and sorting dielectric properties and retrieve the 
        qualified materials. A dielectric is a material that can be polarized by an 
        applied electric field. This limits the dielectric effect to materials with 
        a non-zero band gap. Formally, the dielectric tensor ε relates the externally 
        applied electric field to the field within the material and can be defined as: 
        $$E_i=\sum_j \epsilon^{-1}_{ij}E_{0j}$$ where $$E$$ is the electric field 
        inside the material and $$E_{0}$$ is the externally applied electric field. 
        The dielectric tensors from the Materials Project are calculated from first 
        principles Density Functional Perturbation Theory (DFPT) and are approximated 
        as the superimposed effect of an electronic and ionic contribution $$
        \epsilon_{ij}=\epsilon_{ij}^0+\epsilon_{ij}^\infty$$ 
        From the full piezoelectric tensor, several properties are derived such as the 
        refractive index and potential for ferroelectricity. 
        The mathematical description of the dielectric effect is a tensor constant of 
        proportionality that relates an externally applied electric field to the field 
        within the material. Along with the elastic and piezoelectric tensors, the 
        dielectric tensor provides all the information necessary for the solution of 
        the constitutive equations in applications where electric and mechanical 
        stresses are coupled""",
        )
        .strip()
        .replace("\n", " ")[0]
    )
    args_schema: type[DielectricSchema] = DielectricSchema


class MaterialsPiezoelectric(MPTool):
    name: str = "search_materials_piezoelectric__get"
    description: str = (
        re.sub(
            r"\s+",
            " ",
            """useful when you need piezoelectric properties like piezoelectric 
        tensor, piezoelectric modulus, piezoelectric strain constant, also useful 
        when you need to perform filtering and sorting piezoelectric properties and 
        retrieve the qualified materials. Piezoelectricity is a reversible physical 
        process that occurs in some materials whereby an electric moment is generated 
        upon the application of a stress. This is often referred to as the direct 
        piezoelectric effect. Conversely, the indirect piezoelectric effect refers to 
        the case when a strain is generated in a material upon the application of an 
        electric field. The mathematical description of piezoelectricity relates the 
        strain (or stress) to the electric field via a third order tensor. This tensor 
        describes the response of any piezoelectric bulk material, when subjected to an 
        electric field or a mechanical load""",
        )
        .strip()
        .replace("\n", " ")[0]
    )
    args_schema: type[PiezoSchema] = PiezoSchema


class MaterialsRobocrystallographer(MPTool):
    name: str = "search_materials_robocrys__get"
    description: str = (
        re.sub(
            r"\s+",
            " ",
            """Robocrystallographer is a tool to generate text descriptions of crystal 
            structures. Similar to how a real-life crystallographer would analyse a 
            structure, robocrystallographer looks at the symmetry, local coordination 
            and polyhedral type, polyhedral connectivity, octahedral tilt angles, 
            component-dimensionality, and molecule-within-crystal and fuzzy prototype 
            identification when generating a description""",
        )
        .strip()
        .replace("\n", " ")[0]
    )
    args_schema: type[RobocrysSchema] = RobocrysSchema


class MaterialsOxidation(MPTool):
    name: str = "search_materials_oxidation_states__get"
    description: str = (
        re.sub(
            r"\s+",
            " ",
            """useful when you need possible oxidation states of elements in materials, 
            also useful to sort the results by related materials properties like 
            possible_species, possible_valences, average_oxidation_states, and method 
            for oxidation state prediction""",
        )
        .strip()
        .replace("\n", " ")[0]
    )
    args_schema: type[OxidationSchema] = OxidationSchema


class MaterialsBonds(MPTool):
    name: str = "search_materials_bonds__get"
    description: str = (
        re.sub(
            r"\s+",
            " ",
            """useful when you need bond properties like bond lengths, coordination, 
            also useful when you need to perform filtering and sorting bond properties 
            and retrieve the qualified materials""",
        )
        .strip()
        .replace("\n", " ")[0]
    )
    args_schema: type[BondsSchema] = BondsSchema

class MaterialsTasks(MPTool):
    name: str = "search_materials_tasks__get"
    description: str = (
        re.sub(
            r"\s+",
            " ",
            """useful when you need task_ids of materials and detailed DFT calculation 
            results""",
        )
        .strip()
        .replace("\n", " ")[0]
    )
    args_schema: type[TasksSchema] = TasksSchema

class MaterialsSimilarity(MPTool):
    name: str = "get_by_key_materials_similarity__material_id___get"
    description: str = (
        re.sub(
            r"\s+",
            " ",
            """useful when you need to find similar materials based on a given material 
            id. If you don't have relevant material_id, you should use 
            `MaterialsSummary` tool first""",
        )
        .strip()
        .replace("\n", " ")[0]
    )
    args_schema: type[SimilaritySchema] = SimilaritySchema