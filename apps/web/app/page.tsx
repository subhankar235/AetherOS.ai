import GhostNav from "@/components/landing/GhostNav";
import GrainBackground from "@/components/landing/GrainBackground";
import Hero from "@/components/landing/Hero";
import Problem from "@/components/landing/Problem";
import Stats from "@/components/landing/Stats";
import AgentMap from "@/components/landing/AgentMap";
import TriageBento from "@/components/landing/TriageBento";
import FeaturesBento from "@/components/landing/FeaturesBento";
import Workflow from "@/components/landing/Workflow";
import ApprovalGate from "@/components/landing/ApprovalGate";
import Pricing from "@/components/landing/Pricing";
import FAQ from "@/components/landing/FAQ";
import FinalCTA from "@/components/landing/FinalCTA";
import Footer from "@/components/landing/Footer";

export default function Home() {
  return (
    <>
      <GrainBackground />
      <GhostNav />
      <main>
        <Hero />
        <Problem />
        <Stats />
        <AgentMap />
        <TriageBento />
        <FeaturesBento />
        <Workflow />
        <ApprovalGate />
        <Pricing />
        <FAQ />
        <FinalCTA />
      </main>
      <Footer />
    </>
  );
}
